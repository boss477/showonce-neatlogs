"""DPAPI round trip for .env.enc, in a temp directory so the real file is never touched."""
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock
from showonce import secrets

@unittest.skipUnless(os.name == "nt", "DPAPI is Windows-only")
class SecretsTest(unittest.TestCase):
    def setUp(self):
        self.path = Path(tempfile.mkdtemp(prefix="showonce-secrets-")) / ".env.enc"
        patcher = mock.patch.object(secrets, "ENC_PATH", self.path)
        patcher.start(); self.addCleanup(patcher.stop)

    def test_round_trip_and_ciphertext_hides_values(self):
        secrets.write({"SHOWONCE_TEST_KEY": "not-a-real-secret=with-equals"})
        self.assertNotIn(b"not-a-real-secret", self.path.read_bytes())
        self.assertEqual(secrets.read(), {"SHOWONCE_TEST_KEY": "not-a-real-secret=with-equals"})

    def test_load_does_not_override_existing_env(self):
        secrets.write({"SHOWONCE_TEST_KEY": "from-file"})
        with mock.patch.dict(os.environ, {"SHOWONCE_TEST_KEY": "from-env"}):
            secrets.load()
            self.assertEqual(os.environ["SHOWONCE_TEST_KEY"], "from-env")

if __name__ == "__main__":
    unittest.main()
