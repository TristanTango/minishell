"""Tiny test runner.  Each tests/cases/NAME.msh is run as a MiniShell script and
its stdout is compared with NAME.out.   Run:  python tests/run_tests.py

To add a test: create NAME.msh (commands) and NAME.out (expected stdout).
Write expected output BY HAND first, then check the code against it.
"""
import glob
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def main():
    cases = sorted(glob.glob(os.path.join(ROOT, "tests", "cases", "*.msh")))
    failed = 0
    for script in cases:
        expected_file = script[:-4] + ".out"
        expected = open(expected_file).read() if os.path.exists(expected_file) else ""
        result = subprocess.run([sys.executable, "main.py", script], cwd=ROOT,
                                capture_output=True, text=True, timeout=30)
        ok = result.stdout == expected
        print(("PASS " if ok else "FAIL ") + os.path.basename(script))
        if not ok:
            failed += 1
            print("  expected:", repr(expected))
            print("  got     :", repr(result.stdout))
            if result.stderr:
                print("  stderr  :", repr(result.stderr))
    print(f"\n{len(cases) - failed}/{len(cases)} passed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
