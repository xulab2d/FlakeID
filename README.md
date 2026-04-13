# flakefinder_lab

Deployable MVP for automated 2D material flake discovery on motorized microscopes, with a first-class offline folder mode so the lab can build datasets and validate detection before hardware integration is complete.

## Scope

- Primary targets: `bn90_hbn` and `gr285_graphene`
- MVP target platform: motorized glovebox microscope
- Phase-1 runtime path: folder-based detection and mock scanning
- Phase-2 runtime path: Micro-Manager-backed hardware control
- Training path: COCO-centric dataset export plus manifest/bootstrap tooling for lab-specific retraining

## Selected upstream references

- `2DMatGMM`: baseline detector/classifier behind a wrapper
- `2DMatGMM-System`: parameter/workflow reference only
- `pycro-manager`: Micro-Manager integration path
- `MaskTerial`: future pluggable detector branch for low-contrast materials such as hBN
- `hBN_Detection`: phase-2/phase-3 hBN-specific reference

## Install

```bash
cd flakefinder_lab
python3.10 -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
```

Optional hardware support:

```bash
pip install -e .[hardware]
```

Optional upstream baseline detector stack:

```bash
pip install -e .[baseline]
```

Bootstrap the requested external repos if needed:

```bash
./bootstrap_repos.sh
```

## Quickstart

Folder-based detection:

```bash
flakefinder detect-folder \
  --config configs/bn90_hbn.yaml \
  --input /path/to/images \
  --output runs/bn90_demo
```

Mock scan over a folder-backed tile set:

```bash
flakefinder mock-scan \
  --config configs/mock_bn90_hbn.yaml \
  --input /path/to/mock_tiles \
  --output runs/mock_scan
```

Export candidates:

```bash
flakefinder export-candidates \
  --run runs/mock_scan \
  --format csv
```

Bootstrap a training manifest:

```bash
flakefinder train-bootstrap \
  --manifest data/manifests/bn90_hbn.json
```

## Notes

- The code runs without physical hardware via `MockHardware`.
- RAW/16-bit paths are preserved in metadata; previews and thumbnails are generated separately.
- The `2DMatGMM` wrapper tries to use the cloned upstream repo when available. Install `.[baseline]` to satisfy the common upstream ML dependencies. If the upstream import or model path is unavailable, it falls back to a deterministic heuristic detector so the pipeline remains runnable.
- hBN support is scaffolded for retraining and ranking immediately, but final production performance will depend on collecting lab-specific hBN data.
