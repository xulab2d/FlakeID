import json
import unittest
from pathlib import Path

from flake_ml.config import load_lab_config
from flake_ml.session import initialize_session


class SessionTests(unittest.TestCase):
    def test_initialize_session_creates_manifest_and_directories(self) -> None:
        config_path = Path.cwd() / "configs" / "lab.example.toml"
        output_root = Path.cwd() / "outputs" / "test_temp" / "sessions"
        config = load_lab_config(config_path)

        manifest = initialize_session(
            output_root=output_root,
            config_path=config_path,
            config=config,
            sample_id="graphene_test",
            material="graphene",
            substrate="graphene_285_wet",
            objective="10x",
            operator="tester",
        )

        session_dir = output_root / manifest["session_name"]
        self.assertTrue((session_dir / "session_manifest.json").exists())
        self.assertTrue((session_dir / "config_snapshot.toml").exists())
        self.assertTrue((session_dir / "tiles").exists())
        payload = json.loads((session_dir / "session_manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(payload["sample_id"], "graphene_test")

    def test_initialize_session_sanitizes_directory_name_only(self) -> None:
        config_path = Path.cwd() / "configs" / "lab.example.toml"
        output_root = Path.cwd() / "outputs" / "test_temp" / "sessions"
        config = load_lab_config(config_path)

        manifest = initialize_session(
            output_root=output_root,
            config_path=config_path,
            config=config,
            sample_id="grid 4/23: graphene",
            material="graphene",
            substrate="graphene_285_wet",
            objective="10x",
            operator="tester",
        )

        session_dir = output_root / manifest["session_name"]
        self.assertTrue(session_dir.exists())
        self.assertNotIn("/", manifest["session_name"])
        self.assertNotIn(":", manifest["session_name"])
        payload = json.loads((session_dir / "session_manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(payload["sample_id"], "grid 4/23: graphene")


if __name__ == "__main__":
    unittest.main()
