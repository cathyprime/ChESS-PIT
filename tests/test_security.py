import hashlib
import importlib.util
import os
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path
from unittest.mock import patch

from app.config import secret_setting, settings
from app.runner import engine_argv
from app.security import is_trusted_proxy


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
                         "--runtime runsc", "--cgroup-manager=cgroupfs", "--pull=never",
                         "noexec,nosuid,nodev"):
            self.assertIn(expected, rendered)

    def test_dedicated_container_backend_executes_only_the_verified_stage(self):
        daemon = load_daemon()
        daemon.ENGINE_BACKEND = "container-process"
        staged = Path("/cache/verified-engine")
        self.assertEqual(daemon.command(staged, "live"), [str(staged)])

    def test_dedicated_container_stage_is_executable_after_privilege_drop(self):
        daemon = load_daemon()
        daemon.ENGINE_BACKEND = "container-process"
        with tempfile.TemporaryDirectory() as source, tempfile.TemporaryDirectory() as cache:
            daemon.BOT_DIR, daemon.CACHE_DIR = Path(source), Path(cache)
            key = "C" * 24
            data = b"\x7fELF" + b"container fixture" * 10
            (Path(source) / key).write_bytes(data)
            staged = daemon.cached_engine(key, hashlib.sha256(data).hexdigest())
            self.assertEqual(staged.stat().st_mode & 0o777, 0o505)
            self.assertNotEqual(staged.name, hashlib.sha256(data).hexdigest())


class ProductionConfigurationTests(unittest.TestCase):
    def test_secret_setting_reads_file_without_trailing_newline(self):
        with tempfile.TemporaryDirectory() as directory:
            secret = Path(directory) / "password-hash"
            secret.write_text("$argon2id$example\n")
            with patch.dict(os.environ, {"TEST_HASH_FILE": str(secret)}, clear=True):
                self.assertEqual(secret_setting("TEST_HASH"), "$argon2id$example")

    def test_secret_setting_rejects_ambiguous_sources(self):
        with patch.dict(os.environ, {"TEST_HASH": "direct", "TEST_HASH_FILE": "/tmp/hash"}, clear=True):
            with self.assertRaisesRegex(RuntimeError, "only one"):
                secret_setting("TEST_HASH")

    def test_trusted_proxy_accepts_cidr_and_rejects_outside_address(self):
        proxies = ("127.0.0.1", "172.16.0.0/12")
        self.assertTrue(is_trusted_proxy("172.22.4.9", proxies))
        self.assertTrue(is_trusted_proxy("127.0.0.1", proxies))
        self.assertFalse(is_trusted_proxy("192.0.2.10", proxies))
        self.assertFalse(is_trusted_proxy("not-an-address", proxies))

    def test_invalid_trusted_proxy_fails_startup_validation(self):
        with self.assertRaisesRegex(RuntimeError, "TRUSTED_PROXIES"):
            replace(settings, trusted_proxies=("not-a-network",)).validate()

    def test_production_still_rejects_repository_credentials(self):
        production = replace(settings, environment="production", runner_mode="socket",
                             secure_cookies=True, frontend_origin="https://arena.example.com")
        with self.assertRaisesRegex(RuntimeError, "PASSWORD_HASH"):
            production.validate()


if __name__ == "__main__":
    unittest.main()
