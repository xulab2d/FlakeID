# Donor CAD Workspace

This directory is a curated local workspace of donor CAD files for the `Zeiss Axio` retrofit.

It is not a full mirror of the upstream projects. It is the subset most relevant to:

- `motor housings`
- `motor-side brackets`
- `belt gears / pulleys`
- `focus-drive references`
- `quick-release / stabilizer concepts`

Use this as the design staging area before folding geometry into [`zeiss_axio_cad`](/Users/xulab/Desktop/Flake_Identification/flakefinder_lab/zeiss_axio_cad).

## Directory Layout

- `uc2_motorized_xy_table/`
  - best donor for `NEMA17 XY motor mount`, `belt gears`, and `knob pulley` concepts
- `uc2_micronstage/`
  - best donor for `compact motorized micrometer / focus-style drive` parts
- `puma/`
  - best donor for `focus gears`, `Z motor`, and `quick-release` references
- `manifest.json`
  - source and classification for every copied donor file
- `openflexure_notes/`
  - reserved for future donor references; direct clone failed in this environment

## How To Use This

Default policy:

- `reuse as-is`
  - generic motor housings
  - generic idler/tension hardware
  - generic enclosure and support parts
- `fork and modify`
  - motor-side brackets
  - pulley bodies
  - gear geometry
  - quick-release mechanisms
- `design from scratch`
  - anything that touches the `Zeiss Axio` casting, stage frame, or focus knob geometry directly

## Best Starting Donors

### XY Motorization

Start with:

- `uc2_motorized_xy_table/stl/Assembly_XYTable_Aliepexress_30_XYTable_Aliexpress_motormount_4.stl`
- `uc2_motorized_xy_table/inventor/30_XYTable_Aliexpress_motormount.ipt`
- `uc2_motorized_xy_table/inventor/00_XYTable_large_gear.ipt`
- `uc2_motorized_xy_table/inventor/00_XYTable_medium_gear.ipt`
- `uc2_motorized_xy_table/inventor/00_XYTable_pulley.ipt`

These are the strongest donors for:

- `NEMA17 housing`
- `belt path`
- `gear / pulley proportions`
- `dual-axis stage retrofit layout`

### Focus / Z Concepts

Start with:

- `uc2_micronstage/inventor/cellSTORM_UC2_motorized_micrometer_motormount.ipt`
- `uc2_micronstage/inventor/cellSTORM_UC2_motorized_micrometer_gear1.ipt`
- `uc2_micronstage/inventor/cellSTORM_UC2_motorized_micrometer_gear2.ipt`
- `puma/freecad/Focus_Gears.FCStd`
- `puma/freecad/Z_Motor.FCStd`
- `puma/freecad/QuickRelease_v2.0.FCStd`

These are references for:

- `focus-drive gearing`
- `compact motor mount`
- `disengage / quick-release` ideas

## Important Constraint

Do not try to reuse donor microscope-interface parts directly.

For the `Zeiss Axio`, the following should remain custom:

- stage-side mounting bracket
- focus-side mounting bracket
- exact knob clamp geometry
- exact conical focus sleeve geometry
- any bracket cutouts driven by Axio casting clearance

## Missing / Not Pulled

- `OpenFlexure` donor CAD was not pulled because direct GitHub clone failed in this environment.
- Full upstream repos remain in `_donor_repos/` if you want to inspect more files later.
