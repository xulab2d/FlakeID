from __future__ import annotations

import argparse
from pathlib import Path

from flakefinder.data.exporters import export_candidates
from flakefinder.data.storage import Storage
from flakefinder.pipelines.detect_folder import run_detect_folder
from flakefinder.pipelines.scan_and_detect import run_mock_scan
from flakefinder.pipelines.train_bootstrap import run_train_bootstrap


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="flakefinder")
    subparsers = parser.add_subparsers(dest="command", required=True)

    detect = subparsers.add_parser("detect-folder")
    detect.add_argument("--config", required=True)
    detect.add_argument("--input", required=True)
    detect.add_argument("--output", required=True)

    mock = subparsers.add_parser("mock-scan")
    mock.add_argument("--config", required=True)
    mock.add_argument("--input", required=True)
    mock.add_argument("--output", required=True)

    export = subparsers.add_parser("export-candidates")
    export.add_argument("--run", required=True)
    export.add_argument("--format", choices=["csv", "parquet"], default="csv")

    train = subparsers.add_parser("train-bootstrap")
    train.add_argument("--manifest", required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command == "detect-folder":
        print(run_detect_folder(config_path=args.config, input_dir=args.input, output_dir=args.output))
        return 0
    if args.command == "mock-scan":
        print(run_mock_scan(config_path=args.config, input_dir=args.input, output_dir=args.output))
        return 0
    if args.command == "export-candidates":
        db_path = Path(args.run) / "storage" / "flakefinder.db"
        storage = Storage(db_path)
        try:
            target = export_candidates(storage, Path(args.run) / "exports", args.format)
        finally:
            storage.close()
        print(str(target))
        return 0
    if args.command == "train-bootstrap":
        print(str(run_train_bootstrap(args.manifest)))
        return 0
    parser.error(f"Unknown command: {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
