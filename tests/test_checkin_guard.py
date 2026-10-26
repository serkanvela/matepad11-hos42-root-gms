"""Exercise the guard's timing decisions without touching a device or its clock."""
import pathlib
import os
import shutil
import subprocess
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
BASH = pathlib.Path(r"C:\Program Files\Git\bin\bash.exe") if os.name == "nt" else pathlib.Path(shutil.which("bash") or "/bin/bash")
GUARD = ROOT / "checkin-guard" / "guard.sh"


class GuardPolicyTest(unittest.TestCase):
    def decision(self, now, last_ms, attempt=0):
        p = subprocess.run(
            [str(BASH), "--noprofile", "--norc", "-c",
             '. "$1"; checkin_decision "$2" "$3" "$4"',
             "guard-policy-test", GUARD.as_posix(), str(now), str(last_ms), str(attempt)],
            capture_output=True, text=True, check=False,
        )
        self.assertEqual(p.returncode, 0, p.stderr)
        return p.stdout.strip()

    def test_native_checkin_is_left_alone_before_18_hours(self):
        self.assertEqual(self.decision(100000, 35201000), "fresh")

    def test_checkin_due_at_18_hours(self):
        self.assertEqual(self.decision(100000, 35200000), "stale")

    def test_failed_attempt_is_not_repeated_within_one_hour(self):
        self.assertEqual(self.decision(100000, 10000000, 99999), "backoff")
        self.assertEqual(self.decision(100000, 10000000, 96400), "stale")

    def test_missing_or_invalid_state_does_not_trigger_a_reset(self):
        for value in ("", "bad", "0"):
            self.assertEqual(self.decision(100000, value), "unknown")

    def test_clock_rollback_does_not_trigger_a_checkin_storm(self):
        self.assertEqual(self.decision(100000, 101000000), "clock_skew")
        self.assertEqual(self.decision(100000, 100100000), "fresh")

    def test_real_epoch_milliseconds_are_converted_without_overflow(self):
        self.assertEqual(self.decision(1793041622, 1793041519041), "fresh")


if __name__ == "__main__":
    unittest.main()
