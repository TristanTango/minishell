"""The `deadlock` command.  OWNER: Member 3.

Usage: deadlock detect FILE
       deadlock banker FILE [--request PID r1 r2 ...]
"""


def cmd_deadlock(args, stdin, stdout, stderr):
    stderr.write("deadlock: not implemented yet\n")
    return 1
