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

## What This Does Not Yet Solve

- autofocus for Z
- direct Canon tether capture without a configured external capture command
- robust multilayer thickness regression
- remote model training orchestration
- scan-time stitch mosaics

Those are all outlined in the docs as the next build stages.
