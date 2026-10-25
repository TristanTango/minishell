"""Test runner.   Run:  python tests/run_tests.py

1. Script tests: each tests/cases/NAME.msh is run as a MiniShell script inside a
   FRESH temporary folder (with a copy of samples/ in it) and its stdout is compared
   with NAME.out. Expected output is written BY HAND first, then code is checked.
2. Unit tests: every tests/test_*.py file (unittest).
"""
import glob
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def run_script(script):
    work = tempfile.mkdtemp(prefix="minishell_test_")
    try:
        shutil.copytree(os.path.join(ROOT, "samples"), os.path.join(work, "samples"))
        return subprocess.run([sys.executable, os.path.join(ROOT, "main.py"), script],
                              cwd=work, capture_output=True, text=True, timeout=30)
    finally:
        shutil.rmtree(work, ignore_errors=True)


def run_script_tests():
    cases = sorted(glob.glob(os.path.join(ROOT, "tests", "cases", "*.msh")))
    failed = 0
    for script in cases:
        expected_file = script[:-4] + ".out"
        expected = open(expected_file).read() if os.path.exists(expected_file) else ""
        result = run_script(script)
        ok = result.stdout == expected
        print(("PASS " if ok else "FAIL ") + os.path.basename(script))
        if not ok:
            failed += 1
            print("  expected:", repr(expected))
            print("  got     :", repr(result.stdout))
            if result.stderr:
                print("  stderr  :", repr(result.stderr))
    print(f"\nScript tests: {len(cases) - failed}/{len(cases)} passed\n")
    return failed


def run_unit_tests():
    suite = unittest.defaultTestLoader.discover(os.path.join(ROOT, "tests"),
                                                pattern="test_*.py")
    result = unittest.TextTestRunner(stream=sys.stdout, verbosity=1).run(suite)
    return len(result.failures) + len(result.errors)


def main():
    failed = run_script_tests() + run_unit_tests()
    print("\nALL TESTS PASSED" if failed == 0 else f"\n{failed} FAILED")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
