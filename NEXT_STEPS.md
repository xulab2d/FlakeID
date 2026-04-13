# Next Steps

## Phase 1: folder-based + mock hardware

- run `detect-folder` on historical microscope folders
- tune preprocessing/ranking weights for `bn90_hbn` and `gr285_graphene`
- collect review labels and hard negatives

## Phase 2: Micro-Manager integration

- bind the final glovebox microscope devices
- validate coordinate calibration and focus behavior
- run serpentine scans on a test wafer

## Phase 3: collect our own hBN/graphene data

- capture domain-matched images on the glovebox microscope
- preserve RAW/16-bit imagery and flat/dark references
- annotate useful flakes plus hard negatives
- retrain or fine-tune the detector/filter stack

## Phase 4: optional MaskTerial or hBN branch

- benchmark `MaskTerial` on low-contrast hBN
- evaluate an hBN-specific branch if baseline recall is insufficient
- keep the `Detector` interface stable so deployment does not need restructuring
