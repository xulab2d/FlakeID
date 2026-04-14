# CadQuery Workflow

This directory is the primary CAD path for the Zeiss Axio retrofit.

## Environment

Use the dedicated CAD venv:

```bash
cd /Users/xulab/Desktop/Flake_Identification/flakefinder_lab
source .cad-venv/bin/activate
```

The CAD venv is separate from the app venv because CadQuery currently needs a supported CPython build and a larger geometry stack.

## Directory Layout

- `params.py`: project-wide mechanical parameters
- `models/`: parametric CadQuery model builders
- `scripts/export_models.py`: batch export to `STL` and `STEP`
- `exports/`: generated output files
- `scan_input/`: place microscope scans or derived reference meshes here

## Current Models

- `focus_conical_clamp_pulley`
- `x_stage_split_pulley`
- `y_stage_split_pulley`
- `stage_dual_motor_bracket`
- `focus_motor_bracket`
- `preview_*` arranged layout exports for quick visual inspection

Current Zeiss AXIO stack assumptions:

- `X/Y` stage knobs are coaxial stacked on the same vertical axis
- `Y` is the upper knob
- knob center spacing is about `32 mm`
- belts should route to the `right` side of the microscope
- focus drive should route to the `left` side

## Export

```bash
./.cad-venv/bin/python zeiss_axio_cad/scripts/export_models.py
```

Outputs land in:

- `zeiss_axio_cad/exports/stl`
- `zeiss_axio_cad/exports/step`

## Scan Integration Plan

Once you add the microscope scan to `zeiss_axio_cad/scan_input/`, the next pass should:

1. locate the real knob centers and nearby housing surfaces,
2. design bracket attachment points and motor offsets,
3. route belts with proper clearances,
4. generate bracket/chassis parts around the real scan envelope.
