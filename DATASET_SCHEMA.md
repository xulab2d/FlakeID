# Dataset Schema

## Canonical entities

- `scan`: one acquisition or folder-ingest run
- `tile`: one field-of-view image with acquisition metadata
- `candidate`: one detected flake candidate linked to a tile
- `review`: human validation state for a candidate

## Stored tile metadata

- scan id
- tile id
- x, y, z
- timestamp
- objective
- exposure
- gain
- illumination settings
- substrate/material config key
- raw image path
- preview image path
- focus score
- QC status

## Stored candidate metadata

- candidate id
- tile id
- bbox
- centroid
- optional mask path
- confidence
- predicted material
- predicted thickness/layer bin
- ranking score
- ranking feature dictionary
- review state
- config version
- model version

## Annotation interchange

COCO is the canonical external format.

- images: tiles or review crops
- annotations: flake masks or bboxes
- categories: material/layer classes

## Dataset bootstrap path

1. Run folder detection or mock scan.
2. Export candidate thumbnails and metadata.
3. Perform manual review and relabel positives/hard negatives.
4. Export reviewed data to COCO.
5. Generate manifests for training experiments.
