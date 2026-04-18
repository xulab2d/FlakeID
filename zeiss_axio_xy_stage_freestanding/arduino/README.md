# Arduino Bring-Up

This folder is for quick `XY-only` motion bring-up on the `Zeiss Axio` freestanding pod build.

## What Is Here

- `axio_xy_serial_jogger/axio_xy_serial_jogger.ino`
  - minimal serial command sketch for `Arduino Uno + CNC Shield V3 + DRV8825`
- `GRBL_BRINGUP.md`
  - shortest path from the temporary jog sketch to `GRBL`

## Recommendation

Use this sketch only for:

- first wiring checks
- verifying motor direction
- verifying that the pods can turn the knob pulleys
- rough speed / torque checks

Do not treat it as the final controller for scan automation.

For the real motion stack, use `GRBL`.

## Default Pinout

This sketch assumes standard `CNC Shield V3` pin mappings:

- `X_STEP = D2`
- `Y_STEP = D3`
- `X_DIR = D5`
- `Y_DIR = D6`
- `ENABLE = D8`

## Serial Commands

At `115200` baud:

- `HELP`
- `STATUS`
- `ENABLE`
- `DISABLE`
- `ZERO`
- `X200`
- `Y-150`
- `X800 Y400`
- `X800 Y400 F700`

Meaning:

- `X` and `Y` are relative moves in raw motor steps
- `F` is the delay between step iterations in microseconds

## Tooling

Best choice for fastest first upload:

- `Arduino IDE`

Best choice if you start editing firmware repeatedly:

- `PlatformIO` in `VS Code`

Recommendation:

- use `Arduino IDE` to get the board moving today
- switch to `GRBL` after wiring and direction checks pass
- only bother with `PlatformIO` if you decide to keep a custom sketch alive
