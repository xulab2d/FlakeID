# Zeiss AXIO Scan Notes

## Scan Found

Source mesh:

- [Microscope_Scan.stl](/Users/xulab/Desktop/Flake_Identification/flakefinder_lab/zeiss_axio_cad/scan_input/Microscope_Scan.stl)

Mesh header indicates:

- exported by `Polycam`

## Parsed Mesh Bounds

Raw STL coordinate bounds parsed from the mesh:

- `x`: `-0.6543` to `0.6543`
- `y`: `0.0000` to `1.2310`
- `z`: `-0.4350` to `0.4350`

Overall extents:

- `xlen`: `1.3087`
- `ylen`: `1.2310`
- `zlen`: `0.8700`

## Interpretation

These values are almost certainly in `meters`, not millimeters.

That is consistent with a full microscope-body scan from Polycam:

- width about `1.31 m`
- depth/height envelope about `1.23 m`
- side envelope about `0.87 m`

The mesh is therefore useful immediately for:

- placing a chassis envelope,
- estimating motor-clearance regions,
- planning cable routing,
- deciding which side of the microscope to mount controller hardware.

The mesh is not yet sufficient by itself for final coupler geometry because the knob regions need local accuracy and scale verification.

## What Is Still Needed For Zeiss AXIO Retrofit CAD

Current measured geometry now known:

- focus knob
  - conical
  - `34.12 mm` at end
  - `37.52 mm` at base
  - `26.5 mm` axial length
- stage knobs
  - `X = 27.8 mm`
  - `Y = 32.93 mm`
  - knobs are coaxial and stacked on the same vertical shaft axis
  - `Y` is above `X`
  - center spacing is about `32 mm`
- routing preference
  - `X/Y` belts and motors to the `right`
  - focus belt and motor to the `left`

Still useful to measure or confirm:

- approximate right-side outboard clearance from stage knobs to the nearest obstruction
- approximate left-side outboard clearance from focus knob to the nearest obstruction
- whether the opposite focus knob remains fully accessible once the left-side pulley is mounted
- one close photo showing the stacked `X/Y` knobs in profile

Optional but very useful:

- one ruler or caliper reference photographed against the stage-knob region
- one close-up scan/photo of the stage knobs
- one close-up scan/photo of the focus knob

## Current CAD Status

The CAD pipeline is now based on:

- [zeiss_axio_cad](/Users/xulab/Desktop/Flake_Identification/flakefinder_lab/zeiss_axio_cad)

Existing exported parts are based on the Zeiss Axio measurements captured so far and should still be treated as early workflow validation, not final hardware.
The pulley diameters are now consistent with the Zeiss AXIO measurements, but the bracket/chassis geometry is still pending scan-guided design.

## Next CAD Step

Once the Zeiss knob measurements are available, update the CAD params and generate:

1. confirm right-side and left-side clearance from the scan/photos
2. build a right-side stacked dual-motor bracket envelope for the coaxial `X/Y` drives
3. build a left-side focus motor bracket envelope
4. iterate pulley offsets and belt planes against the real scan
