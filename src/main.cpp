// 918 Technologies Smart Dog Collar - ESP32-S3 reference firmware
// Not validated on-animal; no pet emotion or health claims.
#include <Arduino.h>
#include <Wire.h>
#include <LittleFS.h>
#include <math.h>
#include "driver/i2s.h"
#include "model_enabled.h"
#if ENABLE_BLE
#include <BLEDevice.h>
#include <BLEServer.h>
#include <BLEUtils.h>
#include <BLE2902.h>
#endif

namespace Pins {
constexpr int MIC_BCLK = 5;
constexpr int MIC_WS = 4;
constexpr int MIC_DIN = 6;
constexpr int AMP_BCLK = 7;
constexpr int AMP_WS = 15;
constexpr int AMP_DOUT = 16;
constexpr int I2C_SDA = 8;
constexpr int I2C_SCL = 9;
}
constexpr uint8_t MPU_ADDR = 0x68;
constexpr uint32_t MICROPHONE_HZ = 16000;
constexpr uint32_t SPEAKER_HZ = 22050;
constexpr float BARK_RMS_THRESHOLD = 750.0f; // Must calibrate per mic and dog.
constexpr uint32_t EVENT_COOLDOWN_MS = 2500;
constexpr uint32_t AUDIO_FEEDBACK_GUARD_MS = 800;
constexpr float CLASSIFIER_MIN_CONFIDENCE = 0.70f;
constexpr size_t FRAME = 512;
constexpr uint32_t TELEMETRY_INTERVAL_MS = 1000; // Bench calibration, never raw audio.

static bool micReady = false, speakerReady = false, mpuReady = false, fsReady = false;
static bool currentlyPlaying = false;
static uint32_t lastEventMs = 0, lastPlaybackMs = 0, eventCount = 0;
static uint32_t lastTelemetryMs = 0;

#if ENABLE_BLE
static BLECharacteristic* eventCharacteristic = nullptr;
static BLEServer* bleServer = nullptr;
#endif

static bool setupMic() {
  i2s_config_t cfg = {};
  cfg.mode = (i2s_mode_t)(I2S_MODE_MASTER | I2S_MODE_RX);
  cfg.sample_rate = MICROPHONE_HZ;
  cfg.bits_per_sample = I2S_BITS_PER_SAMPLE_32BIT;
  cfg.channel_format = I2S_CHANNEL_FMT_ONLY_LEFT; // INMP441 L/R strapped LOW
  cfg.communication_format = I2S_COMM_FORMAT_STAND_I2S;
  cfg.intr_alloc_flags = ESP_INTR_FLAG_LEVEL1;
  cfg.dma_buf_count = 8;
  cfg.dma_buf_len = 512;
  cfg.use_apll = false;
  i2s_pin_config_t pins = {};
  pins.bck_io_num = Pins::MIC_BCLK;
  pins.ws_io_num = Pins::MIC_WS;
  pins.data_out_num = I2S_PIN_NO_CHANGE;
  pins.data_in_num = Pins::MIC_DIN;
  if (i2s_driver_install(I2S_NUM_0, &cfg, 0, nullptr) != ESP_OK) return false;
  if (i2s_set_pin(I2S_NUM_0, &pins) != ESP_OK) {
    i2s_driver_uninstall(I2S_NUM_0);
    return false;
  }
  return true;
}

static bool setupSpeaker() {
  i2s_config_t cfg = {};
  cfg.mode = (i2s_mode_t)(I2S_MODE_MASTER | I2S_MODE_TX);
  cfg.sample_rate = SPEAKER_HZ;
  cfg.bits_per_sample = I2S_BITS_PER_SAMPLE_16BIT;
  cfg.channel_format = I2S_CHANNEL_FMT_RIGHT_LEFT;
  cfg.communication_format = I2S_COMM_FORMAT_STAND_I2S;
  cfg.intr_alloc_flags = ESP_INTR_FLAG_LEVEL1;
  cfg.dma_buf_count = 8;
  cfg.dma_buf_len = 256;
  cfg.use_apll = false;
  cfg.tx_desc_auto_clear = true;
  i2s_pin_config_t pins = {};
  pins.bck_io_num = Pins::AMP_BCLK;
  pins.ws_io_num = Pins::AMP_WS;
  pins.data_out_num = Pins::AMP_DOUT;
  pins.data_in_num = I2S_PIN_NO_CHANGE;
  if (i2s_driver_install(I2S_NUM_1, &cfg, 0, nullptr) != ESP_OK) return false;
  if (i2s_set_pin(I2S_NUM_1, &pins) != ESP_OK) {
    i2s_driver_uninstall(I2S_NUM_1);
    return false;
  }
  i2s_zero_dma_buffer(I2S_NUM_1);
  return true;
}

static bool setupMpu() {
  Wire.begin(Pins::I2C_SDA, Pins::I2C_SCL, 100000);
  Wire.beginTransmission(MPU_ADDR);
  Wire.write(0x6B); // PWR_MGMT_1
  Wire.write(0x00); // wake from sleep
  return Wire.endTransmission() == 0;
}

static float readMotionG() {
  if (!mpuReady) return -1.0f;
  Wire.beginTransmission(MPU_ADDR);
  Wire.write(0x3B); // ACCEL_XOUT_H
  if (Wire.endTransmission(false) != 0) return -1.0f;
  if (Wire.requestFrom((int)MPU_ADDR, 6) != 6) return -1.0f;
  const int16_t x = (int16_t)((Wire.read() << 8) | Wire.read());
  const int16_t y = (int16_t)((Wire.read() << 8) | Wire.read());
  const int16_t z = (int16_t)((Wire.read() << 8) | Wire.read());
  const float ax = (float)x / 16384.0f;
  const float ay = (float)y / 16384.0f;
  const float az = (float)z / 16384.0f;
  // Deviation from stationary ~1g; not a direct measure of behavior.
  return fabsf(sqrtf(ax * ax + ay * ay + az * az) - 1.0f);
}

static void playSpeech(const char* label) {
  if (!speakerReady || !fsReady) return;
  // Filenames are selected ONLY from the fixed vocabulary, never raw BLE input.
  const char* file = "/bark.pcm";
  if (strcmp(label, "alert") == 0) file = "/alert.pcm";
  else if (strcmp(label, "attention") == 0) file = "/attention.pcm";
  else if (strcmp(label, "play") == 0) file = "/play.pcm";
  File audio = LittleFS.open(file, "r");
  if (!audio) {
    Serial.printf("audio_missing=%s\n", file);
    audio = LittleFS.open("/bark.pcm", "r");
    if (!audio) return;
  }
  currentlyPlaying = true;
  int16_t mono[256];
  int16_t stereo[512];
  while (audio.available()) {
    const size_t count = audio.read((uint8_t*)mono, sizeof(mono));
    const size_t samples = count / sizeof(int16_t);
    if (!samples) break;
    for (size_t i = 0; i < samples; ++i) {
      // Fixed conservative digital attenuation; still measure real acoustic dBA.
      const int16_t quiet = (int16_t)(mono[i] / 8);
      stereo[2 * i] = quiet;
      stereo[2 * i + 1] = quiet;
    }
    size_t written = 0;
    if (i2s_write(I2S_NUM_1, stereo, samples * 2 * sizeof(int16_t),
                  &written, pdMS_TO_TICKS(1000)) != ESP_OK ||
        written != samples * 2 * sizeof(int16_t)) {
      Serial.println("speaker_i2s_write_error");
      break;
    }
  }
  audio.close();
  i2s_zero_dma_buffer(I2S_NUM_1);
  lastPlaybackMs = millis();
  currentlyPlaying = false;
}

static void notifyEvent(const String& msg, const char* spokenLabel) {
  Serial.println(msg);
#if ENABLE_BLE
  if (eventCharacteristic != nullptr && bleServer != nullptr &&
      bleServer->getConnectedCount() > 0) {
    // Short form fits the default 20-byte BLE ATT notification payload.
    const String shortEvent = String("B|") + spokenLabel;
    eventCharacteristic->setValue(shortEvent.c_str());
    eventCharacteristic->notify();
  }
#else
  (void)spokenLabel;
#endif
}

static void publishEvent(float rms, float zcr, float crest, float motion) {
  float features[4] = {rms, zcr, crest, (motion < 0.0f ? 0.0f : motion)};
  float confidence = 0.0f;
  const char* prediction = DogModel::predict(features, confidence);
  const char* spokenLabel = "bark";
  // Owner-trained classes are observational, not a true language translation.
  if (DogModel::READY && confidence >= CLASSIFIER_MIN_CONFIDENCE &&
      strcmp(prediction, "uncertain") != 0) {
    spokenLabel = prediction;
  }
  String json = "{\"event\":\"bark_like\",\"sequence\":" + String(++eventCount) +
    ",\"label\":\"" + String(DogModel::READY ? prediction : "untrained") +
    "\",\"confidence\":" + String(confidence, 3) +
    ",\"rms\":" + String(rms, 1) +
    ",\"zcr\":" + String(zcr, 3) +
    ",\"crest\":" + String(crest, 2) +
    ",\"motion_g\":" + String(motion, 3) + "}";
  notifyEvent(json, spokenLabel);
  playSpeech(spokenLabel);
}

void setup() {
  Serial.begin(115200);
  delay(350);
  Serial.println("918 Smart Collar reference build (BENCH ONLY)");
  micReady = setupMic();
  speakerReady = setupSpeaker();
  mpuReady = setupMpu();
  fsReady = LittleFS.begin(false); // never silently format recordings/assets
  Serial.printf("mic=%d speaker=%d mpu=%d littlefs=%d trained=%d\n",
                micReady, speakerReady, mpuReady, fsReady, DogModel::READY);
#if ENABLE_BLE
  BLEDevice::init("918 Smart Collar");
  bleServer = BLEDevice::createServer();
  BLEService* svc = bleServer->createService("9f4b3200-9e08-4ad1-bdc1-f98c8617ac01");
  eventCharacteristic = svc->createCharacteristic(
      "9f4b3200-9e08-4ad1-bdc1-f98c8617ac02",
      BLECharacteristic::PROPERTY_READ | BLECharacteristic::PROPERTY_NOTIFY);
  eventCharacteristic->addDescriptor(new BLE2902());
  eventCharacteristic->setValue("ready");
  svc->start();
  BLEAdvertising* advertising = BLEDevice::getAdvertising();
  advertising->addServiceUUID(svc->getUUID());
  advertising->start();
#endif
  if (!micReady) Serial.println("FATAL: microphone I2S did not initialize");
  if (!fsReady) Serial.println("WARNING: generate speech assets and run uploadfs");
  lastEventMs = millis() - EVENT_COOLDOWN_MS;
}

void loop() {
  if (!micReady) { delay(1000); return; }
  static int32_t raw[FRAME];
  size_t received = 0;
  const esp_err_t err = i2s_read(I2S_NUM_0, raw, sizeof(raw), &received,
                                 pdMS_TO_TICKS(200));
  if (err != ESP_OK || received < sizeof(raw)) return;
  float sumsq = 0.0f, peak = 0.0f;
  size_t crosses = 0;
  int16_t previous = 0;
  for (size_t i = 0; i < FRAME; ++i) {
    // INMP441 24-bit left-justified samples in signed 32-bit slots.
    const int16_t v = (int16_t)(raw[i] >> 16);
    const float a = (float)v;
    sumsq += a * a;
    peak = fmaxf(peak, fabsf(a));
    if (i > 0 && ((v >= 0) != (previous >= 0))) ++crosses;
    previous = v;
  }
  const float rms = sqrtf(sumsq / FRAME);
  const float zcr = (float)crosses / (FRAME - 1);
  const float crest = peak / fmaxf(rms, 1.0f);
  const uint32_t now = millis();
  if ((uint32_t)(now - lastTelemetryMs) >= TELEMETRY_INTERVAL_MS) {
    lastTelemetryMs = now;
    Serial.printf("{\"event\":\"telemetry\",\"rms\":%.1f,\"zcr\":%.3f,\"crest\":%.2f,\"motion_g\":%.3f}\n",
                  rms, zcr, crest, readMotionG());
  }
  if (currentlyPlaying || (now - lastPlaybackMs) < AUDIO_FEEDBACK_GUARD_MS ||
      (now - lastEventMs) < EVENT_COOLDOWN_MS) return;
  if (rms >= BARK_RMS_THRESHOLD) {
    lastEventMs = now;
    publishEvent(rms, zcr, crest, readMotionG());
  }
}
