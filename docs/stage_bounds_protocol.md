# Stage Bounds Protocol

## Short Answer

Yes, manual knob motion can help you define the stage bounds for this session.

But no, GRBL will not reliably register that manual motion.

Your current setup is open-loop:

- Arduino UNO
- CNC shield
- GRBL `0.9j`
- no encoder feedback
- homing and soft limits currently disabled

That means GRBL only knows about moves it commanded itself. If you turn the knobs by hand, the controller position becomes untrusted until you re-zero or re-home.

## Important Detail From Today's Probe

On `2026-04-22`, the machine reported:

- `$21=0` hard limits off
- `$22=0` homing off
- `$1=2` step idle delay 2 ms

So the motors release quickly when idle, which means gentle manual turning is probably fine mechanically when the stage is not moving. But the controller still does not "see" the motion.

## Recommended Strategy

Use manual motion only to place the stage at a known physical corner.

Then tell GRBL that this location is your working origin.

After that, use **commanded positive moves only** to map the safe `+X` and `+Y` travel.

Do not discover limits by commanding the motors into the hard stops.

## Safe Procedure

### 1. Start at the lower-left corner by hand

Since you believe the stage is already at minimum `X` and minimum `Y`:

1. Gently confirm that you are really at the lower-left mechanical corner.
2. Back off slightly from the hard stop by hand, about `0.2 mm` to `0.5 mm`.
3. From this point forward, treat that backed-off location as the true session origin.

Why back off:

- avoids riding the belts against the stop
- avoids starting a scan with preload already in the mechanics

## 2. Re-register the controller at this corner

After any manual movement, query status and then set the work origin:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts\grbl_send.ps1 `
  -Port COM3 -Baud 115200 -StartupDelayMs 2000 `
  -Command ? -WaitFor '<' -TimeoutMs 4000
```

Then set the current position to work `X=0`, `Y=0`:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts\grbl_send.ps1 `
  -Port COM3 -Baud 115200 -StartupDelayMs 2000 `
  -Command 'G92 X0 Y0' -WaitFor ok -TimeoutMs 4000
```

If you manually move again after this, repeat the zeroing step.

## 3. Verify axis signs with tiny jogs

Use very small commanded moves first:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts\grbl_send.ps1 `
  -Port COM3 -Baud 115200 -StartupDelayMs 2000 `
  -Command 'G21','G91','G0 X0.05 F60' -WaitFor ok -TimeoutMs 4000
```

That is:

- `G21` millimeters
- `G91` relative mode
- `X0.05` = `50 um`
- `F60` = `60 mm/min`

Do the same for `-X`, `+Y`, and `-Y`, returning to the origin after each test. Confirm the microscope image motion and the stage motion match your expectations.

## 4. Map the safe positive X bound

Once signs are confirmed:

1. Move in `+X` using `1 mm` steps through the interior.
2. When you are within about `5 mm` of the end, switch to `0.2 mm` or `0.5 mm` steps.
3. Stop before any belt tension spike or hard-stop contact.
4. Back off by `0.5 mm` to `1.0 mm`.
5. Record that location as `X_MAX_SAFE`.

Example relative jog:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts\grbl_send.ps1 `
  -Port COM3 -Baud 115200 -StartupDelayMs 2000 `
  -Command 'G21','G91','G0 X1.0 F120' -WaitFor ok -TimeoutMs 4000
```

## 5. Return to origin and map Y the same way

Repeat the same process for `+Y`:

- coarse `1 mm` steps first
- fine `0.2 mm` to `0.5 mm` steps near the edge
- back off `0.5 mm` to `1.0 mm`
- record `Y_MAX_SAFE`

## 6. Use a safety inset, not the raw measured maximum

Once you have the farthest safe visible locations:

- define `safe_min_x = 0`
- define `safe_min_y = 0`
- define `safe_max_x = measured_x_max - 500 um to 1000 um`
- define `safe_max_y = measured_y_max - 500 um to 1000 um`

Those inset values are what should go into the config.

## 7. Save the results in the config

Update [configs/lab.example.toml](../configs/lab.example.toml) or your real lab config:

```toml
[motion]
min_x_um = 0.0
min_y_um = 0.0
max_x_um = 123400.0
max_y_um = 98700.0
safety_margin_um = 1000.0
```

The scan planner will then refuse plans that exceed the configured safe envelope.

## What Manual Motion Is Good For

- placing the stage at a known corner before zeroing
- gently confirming where the physical stops are
- recovering after you intentionally reposition by hand

## What Manual Motion Is Not Good For

- expecting GRBL coordinates to update automatically
- mixing manual and motorized moves without re-zeroing
- defining a trustworthy absolute coordinate system for future sessions

## Best Long-Term Fix

Add real homing switches.

Once homing is enabled:

- you can home at startup
- machine coordinates become repeatable
- soft limits become meaningful
- accidental belt grinding risk drops sharply

Until then, use session-local work coordinates and a conservative safety inset.

