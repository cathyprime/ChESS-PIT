import hashlib
import importlib.util
import tempfile
import unittest
from pathlib import Path

from app.runner import engine_argv


def load_daemon():
    path = Path(__file__).parents[1] / "scripts" / "runner-daemon.py"
    spec = importlib.util.spec_from_file_location("runner_daemon", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class SandboxBoundaryTests(unittest.TestCase):
    def test_uploaded_engine_execution_fails_closed_by_default(self):
        with self.assertRaisesRegex(RuntimeError, "sandbox"):
            engine_argv("/tmp/untrusted", "0" * 64)

    def test_trusted_engine_does_not_use_runner(self):
        self.assertEqual(engine_argv("/trusted/stockfish", trusted=True), ["/trusted/stockfish"])

    def test_runner_rejects_traversal_symlinks_and_digest_mismatch(self):
        daemon = load_daemon()
        with tempfile.TemporaryDirectory() as source, tempfile.TemporaryDirectory() as cache:
            daemon.BOT_DIR, daemon.CACHE_DIR = Path(source), Path(cache)
            key = "A" * 24
            data = b"\x7fELF" + b"safe fixture" * 10
            (Path(source) / key).write_bytes(data)
            digest = hashlib.sha256(data).hexdigest()
            cached = daemon.cached_engine(key, digest)
            self.assertEqual(cached.read_bytes(), data)
            self.assertEqual(cached.stat().st_mode & 0o777, 0o500)
            with self.assertRaises(ValueError):
                daemon.cached_engine("../etc/passwd", digest)
            with self.assertRaises(ValueError):
                daemon.cached_engine(key, "0" * 64)
            link_key = "B" * 24
            (Path(source) / link_key).symlink_to(Path(source) / key)
            with self.assertRaises(ValueError):
                daemon.cached_engine(link_key, digest)

    def test_container_command_has_required_isolation_flags(self):
        daemon = load_daemon()
        args = daemon.command(Path("/private/cache/engine"), "live")
        rendered = " ".join(args)
        for expected in ("--network=none", "--ipc=none", "--read-only",
                         "--cap-drop=all", "--security-opt=no-new-privileges",
                         "--pids-limit=64", "--memory=512m", "--memory-swap=512m",
                         "--runtime runsc", "--pull=never", "noexec,nosuid,nodev"):
            self.assertIn(expected, rendered)


if __name__ == "__main__":
    unittest.main()
