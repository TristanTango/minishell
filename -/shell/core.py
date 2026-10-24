"""Shell core: REPL loop and executor.  OWNER: Member 1 (Shell Lead).

Command contract (everyone must follow it):
    def cmd_xxx(args, stdin, stdout, stderr) -> int
      - write output with stdout.write(...) / stderr.write(...), never print()
      - read input from stdin, never input()
      - never call sys.exit(); return an exit code (0 = success)
"""
import sys

from shell.builtins import BUILTINS
from shell.parser import ASSIGN_RE, ParseError, expand_word, parse
from shell.state import STATE


def run_command(argv, stdin, stdout, stderr):
    """Run ONE simple command (already expanded) and return its exit code."""
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


def run_simple(tokens, stdin, stdout, stderr):
    """Handle assignments and $ expansion, then run one command.

    TODO (Member 1): redirection (> >> < 2> 2>&1) and pipes (|) go here.
    """
    if any(kind == "op" for kind, _ in tokens):
        stderr.write("minishell: pipes and redirection are not supported yet\n")
        return 1

    variables = STATE["vars"]
    i = 0
    # Leading NAME=value words set shell variables (applied in order: A=1 B=$A).
    while i < len(tokens):
        segs = tokens[i][1]
        text, mode = segs[0]
        if mode == "plain" and ASSIGN_RE.match(text):
            name, _, value = expand_word(segs, variables, STATE["last_status"]).partition("=")
            variables[name] = value
            i += 1
        else:
            break

    argv = []
    for _, segs in tokens[i:]:
        word = expand_word(segs, variables, STATE["last_status"])
        if word == "" and all(mode == "plain" for _, mode in segs):
            continue            # an unquoted empty expansion disappears (like Bash)
        argv.append(word)
    return run_command(argv, stdin, stdout, stderr)


def run_line(line, stdin=None, stdout=None, stderr=None):
    """Run one input line (commands joined by ; && ||). Returns the exit code."""
    stdin = stdin or sys.stdin
    stdout = stdout or sys.stdout
    stderr = stderr or sys.stderr
    try:
        items = parse(line)
    except ParseError as e:
        stderr.write(f"minishell: syntax error: {e}\n")
        STATE["last_status"] = 2
        return 2

    status = STATE["last_status"]
    for connector, tokens in items:
        if connector == "&&" and status != 0:
            continue                    # previous failed: skip
        if connector == "||" and status == 0:
            continue                    # previous succeeded: skip
        status = run_simple(tokens, stdin, stdout, stderr)
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
        try:
            run_line(line)
        except Exception as e:  # last line of defence: never crash
            sys.stderr.write(f"minishell: internal error: {e}\n")
    return 0
