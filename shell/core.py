"""Shell core: REPL loop, parser, executor.  OWNER: Member 1 (Shell Lead).

Command contract (everyone must follow it):
    def cmd_xxx(args, stdin, stdout, stderr) -> int
      - write output with stdout.write(...) / stderr.write(...), never print()
      - read input from stdin, never input()
      - never call sys.exit(); return an exit code (0 = success)
"""
import shlex
import sys

from shell.builtins import BUILTINS

# Shell state shared by all commands (variables, last exit code).
STATE = {"vars": {}, "last_status": 0}


def run_command(argv, stdin, stdout, stderr):
    """Run ONE simple command and return its exit code."""
    if not argv:
        return 0
    fn = BUILTINS.get(argv[0])
    if fn is None:
        stderr.write(f"minishell: {argv[0]}: command not found\n")
        return 127
    try:
        return fn(argv[1:], stdin, stdout, stderr)
    except Exception as e:  # the shell must never crash
        stderr.write(f"minishell: {argv[0]}: {e}\n")
        return 1


def run_line(line, stdin=None, stdout=None, stderr=None):
    """Run one input line. Returns the exit code.

    TODO (Member 1), in this order:
      1. variable assignment (NAME=value) and $NAME expansion
      2. ';' then '&&' and '||'
      3. redirection  >  >>  <  2>  2>&1
      4. pipes  |   (run cmd1 into io.StringIO, feed it as stdin to cmd2)
    """
    stdin = stdin or sys.stdin
    stdout = stdout or sys.stdout
    stderr = stderr or sys.stderr
    try:
        argv = shlex.split(line)
    except ValueError as e:
        stderr.write(f"minishell: syntax error: {e}\n")
        return 2
    status = run_command(argv, stdin, stdout, stderr)
    STATE["last_status"] = status
    return status


def main(argv):
    if argv:  # script mode
        with open(argv[0]) as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if line == "exit":
                    break
                run_line(line)
        return 0

    while True:
        try:
            line = input("minishell> ")
        except EOFError:
            print()
            break
        except KeyboardInterrupt:
            print()
            continue
        if line.strip() == "exit":
            break
        run_line(line)
    return 0
