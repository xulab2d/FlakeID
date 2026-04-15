# Zeiss Axio XY-Only Minimal Buy List

This is the cheapest setup I expect to work for the current `XY-only` freestanding-pod design while still giving a clean computer interface.

## Recommendation

Use:

- `USB laptop -> Arduino Uno-compatible board -> CNC Shield V3 -> DRV8825 drivers -> 2x NEMA17 motors`

Why this is the right first build:

- cheapest controller stack that is still standard and well-documented
- direct USB serial control from the computer
- easy to test immediately with `GRBL`
- easy to drive later from Python without adding a Raspberry Pi or vendor-specific controller

What not to buy for this first pass:

- Raspberry Pi just for motion control
- touchscreen CNC pendant
- SD-card offline controller
- focus motor parts

## Buy Now

### Motion Control Electronics

- `1x Arduino Uno-compatible R3 board`
  - cheapest acceptable choice: generic `ATmega328P` Uno-compatible board
  - safer but pricier reference: official Arduino Uno Rev3
  - if you buy a clone, confirm the USB bridge is one your computer can talk to cleanly
- `1x CNC Shield V3`
- `3x DRV8825 stepper driver modules`
  - only `2` are needed for `X/Y`
  - buy `3` so one is a spare
- `1x 12 V 5 A DC power supply`
- `1x USB cable` matching the Uno board you buy
- `1x 100 uF or larger electrolytic capacitor`, `35 V` or higher
  - place it close to `VMOT/GND` on the shield

### Motors / Belt Drive

- `2x NEMA17` bipolar stepper motors
  - target spec:
    - `42 x 42 mm` face
    - `5 mm` shaft
    - about `1.5-1.7 A` per phase
    - at least about `40 N*cm` holding torque
- `2x GT2 20T` metal pulleys
  - `5 mm` bore
  - `6 mm` belt width
- `1x small assortment of GT2 closed-loop belts`
  - `6 mm` wide
  - buy an assortment rather than a single length on the first pass
  - practical first range: about `400-600 mm` loop lengths

### Printed-Part Assembly Hardware

- `8x M3 x 10 mm` socket-head screws for motor mounting
- `4x M5 x 25 mm` socket-head screws for motor-plate-to-pod mounting
- `4x M5 hex nuts`
- `8x M5 washers`
- `3x M3 x 65 mm` socket-head screws for the `X` pulley clamp
- `3x M3 x 70 mm` socket-head screws for the `Y` pulley clamp
- `6x M3 hex nuts` for the pulley clamps
- `12x M3 washers` for the pulley clamps

Note:

- those long `M3` lengths come directly from the current pulley geometry
- if your local hardware source has poor availability in those exact lengths, buying a nearby longer length and using extra washers is acceptable

### Grip / Friction Materials

- `1x` sheet of `1.0 mm` adhesive-backed `nitrile` or `polyurethane` rubber
  - this is the pulley liner material
  - cut it by hand to fit the knob bore

### Wiring / Small Parts

- `2x` 4-wire stepper extension cables if the motors do not ship with long enough leads
- `18-22 AWG` hookup wire for power if your supply does not come ready to land on the shield
- `assorted zip ties`

### Ballast

- dense ballast for each pod base
  - cheapest good option is scrap steel
  - stacked steel washers or short steel bar stock is fine

## Minimal Quantity Summary

- `1x` Uno-compatible controller
- `1x` CNC Shield V3
- `3x` DRV8825
- `1x` 12 V / 5 A supply
- `2x` NEMA17 motors
- `2x` GT2 20T 5 mm pulleys
- `1x` assortment of `6 mm` GT2 closed-loop belts
- `8x` M3 x 10 motor screws
- `4x` M5 x 25 pod screws
- `3x` M3 x 65 pulley screws
- `3x` M3 x 70 pulley screws
- `1x` rubber liner sheet

## Software / Control Path

Use this bring-up path:

1. flash `GRBL` onto the Uno-compatible board
2. verify manual jogging over USB from the computer
3. test both motors with the freestanding pods on the table
4. after that, talk to `GRBL` directly from Python over serial

For the first tests:

- use `Universal Gcode Sender` or another simple `GRBL` sender to verify motion
- then switch to Python serial control for integration with `flakefinder_lab`

## Cheapest Version I Would Actually Buy

If I were ordering today for the current design, I would buy:

- generic `Uno-compatible` board
- generic `CNC Shield V3`
- `Pololu DRV8825` drivers instead of the very cheapest no-name driver modules
- generic `NEMA17` motors matching the spec above
- generic metal `GT2 20T 5 mm` pulleys
- cheap closed-loop `GT2 6 mm` belt assortment
- decent `12 V 5 A` supply from a reputable seller

That is the best cost/performance split for a fast first build.

## Notes On Confidence

Observation:

- `GRBL` explicitly targets Arduino boards with a `328p` processor.
- `DRV8825` modules are standard step/dir drivers and are drop-in compatible with many CNC shield setups.
- `pySerial` gives a direct Python serial path from the lab computer to the controller.

Inference:

- the cheapest place to save money is the `Uno-compatible board`, `CNC shield`, and generic pulleys
- the place I would avoid going too cheap is the stepper drivers and power supply

## Reference Sources

- Arduino Uno Rev3:
  - https://store.arduino.cc/products/arduino-uno-rev3
- CNC Shield V3:
  - https://handsontec.com/index.php/product/cnc-shield-v3-for-arduino/
- DRV8825:
  - https://www.pololu.com/product/2133/
- NEMA17 reference motor:
  - https://us.openbuilds.com/nema-17-stepper-motor/
- GT2 20T 5 mm pulley:
  - https://www.servocity.com/2mm-pitch-gt2-pinion-timing-pulley-5mm-bore-20-tooth/
- 12 V 5 A supply:
  - https://www.adafruit.com/product/352
- GRBL:
  - https://github.com/gnea/grbl
- pySerial:
  - https://pyserial.readthedocs.io/en/latest/
