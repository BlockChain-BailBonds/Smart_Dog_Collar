# Hardware, wiring and power — reference ESP32-S3 carrier

**GPIOs below are example firmware assignments, NOT claims about your specific bare S3-MINI module PCB.** Verify actual accessible GPIO pins, 3.3 V logic, regulator output, connectors and strap/USB/flash restrictions from your physical carrier. **Never apply a battery directly to an ESP32 GPIO or 3V3 rail.**

## Wiring map

| Peripheral | Signal | ESP32-S3 GPIO / rail | Notes |
| --- | --- | --- | --- |
| INMP441 | VDD / GND | 3V3 / GND | I2S microphone, 3.3 V only |
| INMP441 | SCK (BCLK) | GPIO5 | Clock from I2S0 |
| INMP441 | WS | GPIO4 | Word select |
| INMP441 | SD | GPIO6 | Data into MCU |
| INMP441 | L/R | GND | Enables LEFT-slot capture |
| INMP441 | CHIPEN, if exposed | 3V3 | Enabled high on applicable modules |
| MAX98357A | VIN / GND | regulated 3V3 / GND | Share ground, ensure rail current headroom |
| MAX98357A | BCLK | GPIO7 | I2S1 transmit clock |
| MAX98357A | LRC / LRCLK | GPIO15 | Word select |
| MAX98357A | DIN | GPIO16 | Serial audio |
| MAX98357A | SPK+ / SPK- | 8 Ω speaker terminals | **Do not connect SPK- to GND** |
| MPU6050 | VCC / GND | 3V3 / GND | Verify breakout board's power/level shifting |
| MPU6050 | SDA | GPIO8 | Shared I2C |
| MPU6050 | SCL | GPIO9 | Shared I2C |
| MPU6050 | AD0 | GND | Assumes address 0x68 |

Verify INMP441 L/R low, and MAX98357A gain/SD/channel-mode jumper or pin requirements on your chosen breakout. Input/output are **two separate I2S controllers**. This firmware does not support a generic analog microphone or an ESP32-C3 as a drop-in replacement.

## Power path (bench prototype)

Protected 1S battery -> compatible charger/protection/power-path circuitry -> current-rated regulated 3.3 V **buck-boost** -> development board's documented 3V3 power input, mic, amp, MPU6050.

If you use USB on a dev board while attaching external 3V3, verify the carrier's power-source selection and backfeed protection; do not indiscriminately feed both. Battery charging is off-animal. TP4056 is a charging IC, **not** a full protection/power-path/regulation design. Size regulator and cell for radio/audio peaks; verify thermal behavior, brownouts and battery undervoltage cutoff with actual measurements.

Never solder directly to a loose unprotected 18650. Use certified protected cells and correctly engineered holders/charging circuits. No production power PCB/netlist is supplied. The earlier 3500 mAh 18650 specification is a candidate, not a measured endurance claim.

## Optional experimental expansions (NOT in baseline firmware)

- MAX86150 PPG/ECG: animal fur and electrode contact interfere with measurements; **do not infer heart rate, distress or clinical status without veterinary validation**.
- GPS: separate GNSS receiver, antenna, UART and privacy policy required.
- BLE/mobile: gated by build flag. See SETUP.md.
- ESP32-LyraT: alternative audio board requires new pin/driver configuration.
- 3D enclosure: measurements, ventilation, waterproofing and breakaway hardware remain mechanical validation work; **no fit-tested case or PCB fabrication files are claimed here**.

## Bench acceptance checklist

1. Confirm each rail with a multimeter before connecting the S3.
2. Confirm mic I2S captures RMS above the ambient baseline on a gentle clap/test source.
3. Confirm MPU6050 is detected and reports changing motion.
4. Generate/upload PCM files and measure speaker output with the speaker **away from the dog's ears**.
5. Check no feedback causes repeated self-triggering; set threshold/cooldown for environment.
6. Log supply peaks, temperature and continuous runtime.
7. Test enclosure mechanical strain, chew resistance, ingress, secure/breakaway attachment, snagging and pressure points.
8. Only consider supervised short-duration wear after independent safety review.

Useful chip references: https://docs.espressif.com/projects/esp-idf/en/stable/esp32s3/api-reference/peripherals/i2s.html and https://www.analog.com/en/products/max98357a.html .
