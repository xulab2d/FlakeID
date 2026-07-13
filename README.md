# FlakeID

`flake-ml` is the starter software stack inside `FlakeID`, a research-backed framework for automated optical discovery of exfoliated 2D material flakes on a motorized microscope. It is designed around your current setup:

- Microscope: Zeiss AXIO Imager.A2m
- Motion: Arduino UNO + CNC shield running GRBL
- Camera: Canon DS126571 over USB
- Primary materials:
  - graphene on 285 nm Si/SiO2 (wet)
  - hBN on 90 nm Si/SiO2 (dry)

This repository focuses on the parts we can build immediately on the local workstation:

- serpentine scan planning
- GRBL integration hooks
- flat-field and background correction
- lightweight flake-candidate detection on CPU
- scan cataloging and COCO export for future training
- a practical data and human-in-the-loop plan

It also leaves clean interfaces for stronger models and remote training later.

## Repository Layout

- [docs/research_review.md](docs/research_review.md)
- [docs/system_architecture.md](docs/system_architecture.md)
- [docs/data_and_human_loop.md](docs/data_and_human_loop.md)
- [docs/bringup_checklist.md](docs/bringup_checklist.md)
- [docs/scanning_protocol.md](docs/scanning_protocol.md)
- [docs/stage_bounds_protocol.md](docs/stage_bounds_protocol.md)
- [docs/stage_calibration_ui.md](docs/stage_calibration_ui.md)
- [docs/camera_pathway.md](docs/camera_pathway.md)
- [docs/data_collection_workflow.md](docs/data_collection_workflow.md)
- [docs/drift_correction.md](docs/drift_correction.md)
- [docs/hardware_probe_notes.md](docs/hardware_probe_notes.md)
- [docs/repo_push_setup.md](docs/repo_push_setup.md)
- [configs/lab.example.toml](configs/lab.example.toml)
- [scripts/grbl_send.ps1](scripts/grbl_send.ps1)
- `src/flake_ml`: package code
- `tests`: lightweight regression tests

## Quick Start

Use the bundled Python runtime already available on this machine:

```powershell
& 'C:\Users\xulab\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -m flake_ml.cli --help
```

Create a scan plan:

```powershell
& 'C:\Users\xulab\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -m flake_ml.cli scan-plan `
  --config configs/lab.example.toml `
  --width-mm 8 `
  --height-mm 8 `
  --output outputs/scan_plan.json
```

Open the stage calibration UI:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts\launch_stage_ui.ps1 `
  -Config configs/lab.example.toml
```

Run a capture scan over a saved scan ROI:

```powershell
& 'C:\Users\xulab\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -m flake_ml.cli run-scan `
  --config configs/lab.example.toml `
  --sample-id graphene_grid_001 `
  --material graphene `
  --substrate graphene_285_wet `
  --objective 10x
```

Detect candidates in one image:

```powershell
& 'C:\Users\xulab\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -m flake_ml.cli detect-image `
  path\to\image.jpg `
  --config configs/lab.example.toml `
  --output-json outputs\image_candidates.json `
  --overlay outputs\image_overlay.png
```

Probe the connected camera and installed Canon tooling:

```powershell
& 'C:\Users\xulab\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -m flake_ml.cli camera-probe
```

Create a session scaffold for a new data-collection run:

```powershell
& 'C:\Users\xulab\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -m flake_ml.cli init-session `
  --config configs/lab.example.toml `
  --output-root outputs\sessions `
  --sample-id graphene_trial_001 `
  --material graphene `
  --substrate graphene_285_wet `
  --objective 10x `
  --operator xulab
```

Estimate residual overlap shift between neighboring tiles:

```powershell
& 'C:\Users\xulab\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -m flake_ml.cli estimate-shift `
  path\to\left_tile.jpg `
  path\to\right_tile.jpg `
  --axis x `
  --overlap-fraction 0.12
```

Score a z-stack or focus bracket with autofocus metrics:

```powershell
& 'C:\Users\xulab\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -m flake_ml.cli focus-score `
  path\to\zminus.jpg `
  path\to\z0.jpg `
  path\to\zplus.jpg `
  --metric tenengrad `
  --crop-fraction 0.5
```

Replay a folder of microscope images into a catalog:

```powershell
& 'C:\Users\xulab\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -m flake_ml.cli replay-folder `
  path\to\images `
  --config configs/lab.example.toml `
  --catalog outputs\flakes.db `
  --sample-id graphene_trial_001 `
  --material graphene
```

Export reviewed candidates to COCO:

```powershell
& 'C:\Users\xulab\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -m flake_ml.cli export-coco `
  --catalog outputs\flakes.db `
  --output outputs\coco_candidates.json
```

Open the manual review UI for a scan session:

```powershell
& 'C:\Users\xulab\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -m flake_ml.cli review-images `
  --session-dir photos\scans\20260424T024315Z_flake_grid_001
```

Launch the polygon-aware napari reviewer for precise flake boundaries:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts\launch_napari_review.ps1 `
  -SessionDir photos\scans\20260424T024315Z_flake_grid_001
```

Use napari polygon mode for irregular flake outlines and rectangle mode only for quick coarse labels. The napari reviewer saves polygon vertices directly into the same `manual_annotations.json` file, so later COCO exports keep the real outline instead of collapsing everything to crude boxes.

Recommended tile labels:

- `flake_present`: the field contains one or more flakes worth annotating
- `empty_substrate`: true negative on the correct substrate with no flake present
- `off_target`: the stage is between sites or otherwise not over a useful survey location
- `bad_focus`: the field is not trustworthy because focus failed
- `artifact`: dust, glare, tape residue, edge effects, or other nuisance structure
- `unsure`: reviewer cannot confidently decide yet

Object labels stay flake-specific: `graphene`, `hbn`, `other_flake`, and `artifact`.

The napari reviewer also supports object-level metadata for downstream ranking:

- `thickness_bin`: `unknown`, `mono`, `bi`, `few_layer`, `thick`
- `size_class`: `unknown`, `tiny`, `small`, `usable`, `large`
- `shape_class`: `unknown`, `bottom_gate_candidate`, `channel_candidate`, `irregular`, `fragmented`
- `priority`: `unknown`, `ignore`, `review`, `device_candidate`

Set those in the dock and click `Apply Metadata To Selected` after selecting one or more flakes.

Reviewer navigation tips:

- reopening the same session resumes at the most recently saved image
- type an image number or filename fragment in the jump box and press `Enter`
- `[` and `]` move backward and forward
- `Ctrl+L` focuses the jump box
- `Ctrl+G` jumps to the typed image
- `Ctrl+J` jumps back to the saved resume target

Export manual review polygons or boxes to COCO:

```powershell
& 'C:\Users\xulab\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -m flake_ml.cli export-manual-coco `
  --review-path photos\scans\20260424T024315Z_flake_grid_001\labels\manual_annotations.json `
  --output outputs\manual_annotations.coco.json
```

## Photo Storage

- `photos/incoming`: fallback hot folder for EOS Utility download handoff
- `photos/scans/<timestamp>_<sample_id>`: one folder per scan with tiles, logs, QC, and catalog files
- `photos/scans/<timestamp>_<sample_id>/labels/manual_annotations.json`: manual flake review output from the Tk reviewer or the napari polygon reviewer

The `photos/` tree is gitignored.

## Direct Canon Capture

The preferred camera path on this workstation is now the local Canon SDK helper:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts\canon_sdk_capture.ps1 -Probe
```

For a direct still-image test:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts\canon_sdk_capture.ps1 `
  -Output outputs\camera_test.jpg
```

Close `EOS Utility` or any Canon live-view window before using the direct SDK path, because the camera session is exclusive.

## What This Does Not Yet Solve

- autofocus for Z
- robust multilayer thickness regression
- remote model training orchestration
- scan-time stitch mosaics

Those are all outlined in the docs as the next build stages.
