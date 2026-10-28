"""Run the JVM boundary test without an Android device or Xposed runtime."""
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class GmsCompatibilityPolicyTest(unittest.TestCase):
    def test_scope_version_and_callback_boundaries(self):
        with tempfile.TemporaryDirectory(prefix="dbyw09-gmscompat-policy-") as output:
            self.assertTrue(Path(output).resolve().is_relative_to(Path(tempfile.gettempdir()).resolve()))
            sources = [
                ROOT / "gmscompat/src/local/dbyw09/gmscompat/CompatPolicy.java",
                ROOT / "tests/java/CompatPolicyTest.java",
            ]
            compiled = subprocess.run(["javac", "-d", output, *map(str, sources)], capture_output=True, text=True)
            self.assertEqual(compiled.returncode, 0, compiled.stderr)
            tested = subprocess.run(["java", "-cp", output, "CompatPolicyTest"], capture_output=True, text=True)
            self.assertEqual(tested.returncode, 0, tested.stdout + tested.stderr)
            self.assertIn("PASS:", tested.stdout)


if __name__ == "__main__":
    unittest.main()
