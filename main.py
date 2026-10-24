"""MiniShell entry point.

Usage:
    python main.py              interactive prompt
    python main.py script.msh   run commands from a file (no prompt, used by tests)
"""
import sys
from shell.core import main

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
