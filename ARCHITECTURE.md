# Architecture

## Design choices

`flakefinder_lab` is split into five boundaries:

1. `hardware`: vendor-agnostic control contracts for camera, XY stage, focus, and illumination.
2. `acquisition`: tile planning, scan traversal, autofocus hooks, and revisit scheduling.
3. `imaging`: RAW/16-bit ingest and deterministic preprocessing/QC.
4. `detection`: pluggable detectors, false-positive filtering, and ranking logic.
5. `data`: SQLite-backed run storage plus COCO/manifest/export helpers.

## Core principles

- Acquisition and offline folder detection are decoupled.
- Hardware specifics live behind interfaces and adapters.
- The detector is replaceable without rewriting the pipeline.
- Results are stored locally as files plus a queryable SQLite database.
- Dataset generation is a first-class concern from day one.

## Baseline detector strategy

- Initial baseline: `2DMatGMM` wrapper.
- Real blocker: upstream pretrained assets do not cleanly cover every lab/material/domain combination, especially hBN on the glovebox microscope.
- Practical response: keep the upstream wrapper in place, but allow controlled fallback to a heuristic detector and prepare retraining/export flows immediately.

## End-to-end flow

1. Load substrate/material config.
2. Generate scan plan or enumerate folder tiles.
3. Acquire/load RAW or 16-bit tile image.
4. Apply configurable preprocessing.
5. Compute focus/QC metrics.
6. Run detector and optional false-positive filter.
7. Rank candidates with substrate-specific weights.
8. Persist tile/candidate metadata, previews, crops, and exports.
9. Export manifests/COCO for review and retraining.
