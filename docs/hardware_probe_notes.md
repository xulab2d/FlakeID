# Hardware Probe Notes

Date: `2026-04-22`

These notes were collected directly from the microscope control computer without moving the stage.

## GRBL Reachability

- `COM3` responds as `Grbl 0.9j`
- a status probe returned:
  - `<Idle,MPos:0.000,0.000,0.000,WPos:-1.050,-3.000,0.000>`

This means the Arduino/GRBL side is reachable from the workstation.

## Reported GRBL Settings

- `$100=250.000` x steps/mm
- `$101=250.000` y steps/mm
- `$102=250.000` z steps/mm
- `$110=200.000` x max rate mm/min
- `$111=500.000` y max rate mm/min
- `$112=500.000` z max rate mm/min
- `$120=10.000` x accel mm/s^2
- `$121=10.000` y accel mm/s^2
- `$122=10.000` z accel mm/s^2
- `$130=200.000` x max travel mm
- `$131=200.000` y max travel mm
- `$132=200.000` z max travel mm

## Immediate Implications

- GRBL coordinates are in `mm`, so the software layer should expose microns internally but convert to millimeters at the hardware boundary.
- The current default travel rate in the config, `2500 um/s`, corresponds to `150 mm/min`, which is under the current x-axis max rate of `200 mm/min`.
- Early scan tests should stay comfortably below the configured x-axis maximum until real motion is validated on the microscope.

## Recommended Next Hardware Test

1. Unlock GRBL if needed.
2. Jog `50 um` in `+X`, then return.
3. Jog `50 um` in `+Y`, then return.
4. Confirm the microscope image motion matches the expected axis signs.
5. Only then attempt a `3 x 3` image overlap test.

