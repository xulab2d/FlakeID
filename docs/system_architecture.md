# System Architecture

## Goal

Turn a motorized optical microscope into a reliable flake-scanning instrument that can:

1. move reproducibly across a sample,
2. capture tiles with stable metadata,
3. detect likely flakes,
4. rank them for review or revisits,
5. accumulate training data for stronger models.

## Architecture

### 1. Motion Layer

Responsibilities:

- connect to GRBL on the Arduino UNO
- home and unlock safely
- move to absolute XY positions
- wait for idle before capture

Implementation in this repository:

- `flake_ml.motion.base.MotionController`
- `flake_ml.motion.grbl.PowerShellGrblController`
- `flake_ml.motion.pyserial_grbl.PySerialGrblController`
- `scripts/grbl_send.ps1`

Why this design:

- `pyserial` is not guaranteed on this machine, but PowerShell can access `System.IO.Ports.SerialPort` directly on Windows.
- The PowerShell path is useful for probing or one-off diagnostics.
- Real automated scanning should use the persistent `PySerialGrblController`, because reopening the serial port can reset an Arduino UNO running GRBL.

## 2. Camera Layer

Responsibilities:

- trigger a capture
- save the image to a known path
- attach tile metadata

Implementation in this repository:

- `flake_ml.acquisition.base.Camera`
- `flake_ml.acquisition.command.ExternalCommandCamera`
- `flake_ml.acquisition.command.DirectoryReplayCamera`

Why this design:

- Canon tethering is the least stable part of the current setup because the exact Windows-side control path is still unknown.
- An external command interface lets you plug in EOS Utility, Canon SDK tooling, `gphoto2`, or any future wrapper without touching the rest of the pipeline.

## 3. Scan Planner

Responsibilities:

- convert sample bounds and field of view into a tile grid
- use a serpentine path to reduce wasted stage travel
- preserve stage coordinates for every image

Implementation:

- `flake_ml.scanning.planner.build_serpentine_plan`

## 4. Preprocessing

Responsibilities:

- flat-field correction
- white-balance normalization
- slow-varying background estimation
- stable inputs for classical and learned detectors

Implementation:

- `flake_ml.processing.preprocess`

## 5. Detection

Responsibilities:

- generate conservative candidate regions from a tile
- score candidates for review
- compute features for later clustering or learning

Implementation:

- `flake_ml.detection.classical.ClassicalFlakeDetector`
- `flake_ml.detection.components`
- `flake_ml.processing.features`

Current algorithm:

- estimate background by downsampling and re-expanding the image
- measure robust color/saturation/luminance deviations
- build a candidate mask
- clean it with simple morphology
- run connected components
- compute component statistics
- assign heuristic scores

Why this first:

- It is fast on CPU.
- It gives you useful candidates before you have training data.
- It produces structured features that can seed later GMM or supervised models.

## 6. Catalog

Responsibilities:

- store scans, tiles, and candidates
- track review labels
- export training data

Implementation:

- `flake_ml.catalog.CatalogStore`

Database:

- SQLite via the Python standard library

Stored objects:

- scans
- tiles
- candidates

## 7. Learning Layer

Responsibilities:

- weakly supervised clustering of candidate appearance
- binary acceptance ranking from reviewed examples

Implementation:

- `flake_ml.learning.gmm.GaussianMixtureModel`
- `flake_ml.learning.logistic.LogisticRegressor`

Why this matters:

- It gives you a useful middle layer between pure heuristics and a full deep network.
- It is appropriate for the small-data phase.

## 8. Annotation Export

Responsibilities:

- turn reviewed candidates into standard training formats

Implementation:

- `flake_ml.annotation.coco.export_catalog_to_coco`

Why COCO:

- most segmentation/detection toolchains can consume it directly or convert from it easily
- it keeps the path open to Mask R-CNN, Detectron2, MaskTerial, or other modern stacks

## Recommended Deployment Stages

### Stage 0

- wire hardware
- confirm GRBL communication
- confirm reproducible field of view

### Stage 1

- run folder replay on existing microscope images
- tune candidate thresholds
- validate catalog and review flow

### Stage 2

- live XY scanning
- save every tile with stage coordinates
- human review loop for accepted/rejected candidates

### Stage 3

- fit GMM or simple acceptance model
- prioritize likely flakes instead of all candidates equally

### Stage 4

- train or fine-tune segmentation on cluster/GPU machine
- deploy the compact inference model back to the microscope PC

### Stage 5

- add autofocus and revisit logic
- optionally add active search policies or contextual bandits
