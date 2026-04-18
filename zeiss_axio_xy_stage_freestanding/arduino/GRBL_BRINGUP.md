# GRBL Bring-Up For Zeiss Axio XY Pods

This is the shortest path from the current working `Uno + CNC Shield V3 + A4988` bench setup to `GRBL`.

## Recommendation

Use:

- `Arduino IDE 2` to flash `GRBL`
- `Universal Gcode Sender` for first jogging from the computer

This is the fastest practical path for the current setup.

## What To Install

### 1. Arduino IDE 2

- https://www.arduino.cc/en/software

### 2. GRBL source

- official repo: https://github.com/gnea/grbl
- release/source page: https://github.com/gnea/grbl/releases

### 3. Universal Gcode Sender

- https://winder.github.io/ugs_website/
- GitHub: https://github.com/winder/Universal-G-Code-Sender

## Flashing GRBL To The Uno

### Option A: Arduino IDE library install path

1. Download `grbl` from the official repository.
2. Unzip it.
3. Find the `grbl` folder inside the download.
4. In Arduino IDE:
   - `Sketch -> Include Library -> Add .ZIP Library...`
   - or place the `grbl` library folder into your Arduino libraries folder
5. Restart Arduino IDE if needed.
6. Open:
   - `File -> Examples -> grbl -> grblUpload`
7. In `Tools`:
   - `Board -> Arduino Uno`
   - `Port ->` select your Uno
8. Click `Upload`

If upload succeeds, the Uno should now be running `GRBL`.

### Option B: Flash prebuilt hex

The `gnea/grbl` releases also provide precompiled `.hex` files, but for your current setup the Arduino IDE library path is simpler.

## First Connection Test

1. Keep:
   - `USB` connected
   - `12 V` motor supply connected
   - one known-good `A4988` installed
   - one known-good motor connected first
2. Open `UGS`
3. Connect to the Uno serial port
4. Set baud rate to:
   - `115200`

You should see a `Grbl` welcome banner.

## First Commands

In the UGS console, send:

```text
$$
? 
```

Meaning:

- `$$` prints settings
- `?` prints current state

## First Safe Motion Setup

Before any real jogging:

- keep the motor unloaded if possible
- use a known-good driver
- use conservative motion settings

Useful starter settings for bench testing on an unloaded axis:

```text
$110=200
$111=200
$120=10
$121=10
```

Meaning:

- `$110`, `$111`: max rate for `X`, `Y`
- `$120`, `$121`: acceleration for `X`, `Y`

These are intentionally conservative first values.

## Steps/mm

For now, do not worry about correct `steps/mm`.

Just use a temporary value so jogging works:

```text
$100=100
$101=100
```

Later, once the pulleys and belt path are finalized, measure actual travel and calibrate `X` and `Y`.

## First Jogging

Use the UGS jog controls or send very small relative moves.

If you need to reverse one axis:

```text
$3=1
```

or

```text
$3=2
```

or for both:

```text
$3=3
```

`$3` controls axis direction invert bits.

## Practical Sequence I Recommend

1. Flash `GRBL`.
2. Confirm the welcome banner appears.
3. Connect only `X`.
4. Set conservative values:

```text
$100=100
$110=200
$120=10
```

5. Jog `X`.
6. If stable, repeat for `Y`.
7. Then connect both axes and test together.

## Why GRBL Is Better Than The Temporary Sketch

`GRBL` already gives you:

- proper acceleration/deceleration
- stable serial command handling
- standard CNC motion behavior
- easy later Python control from the computer

That is why it is the right next step once the motors are basically alive.

## References

- `gnea/grbl`:
  - https://github.com/gnea/grbl
- Compiling GRBL:
  - https://github-wiki-see.page/m/gnea/grbl/wiki/Compiling-Grbl
- Universal Gcode Sender:
  - https://github.com/winder/Universal-G-Code-Sender
