"""Built-in commands and the command registry.  OWNER: Member 1.

Every command takes (args, stdin, stdout, stderr) and returns an exit code.
Other members register their commands at the bottom of this file.
"""
import os

from shell.state import STATE


def cmd_pwd(args, stdin, stdout, stderr):
    stdout.write(os.getcwd() + "\n")
    return 0


def cmd_echo(args, stdin, stdout, stderr):
    stdout.write(" ".join(args) + "\n")
    return 0


def cmd_cd(args, stdin, stdout, stderr):
    target = args[0] if args else os.path.expanduser("~")
    try:
        os.chdir(target)
    except OSError as e:
        stderr.write(f"cd: {target}: {e.strerror}\n")
        return 1
    return 0


def cmd_env(args, stdin, stdout, stderr):
    """List the shell variables set with NAME=value."""
    if args:
        stderr.write("env: takes no arguments\n")
        return 1
    for name, value in STATE["vars"].items():
        stdout.write(f"{name}={value}\n")
    return 0


def cmd_help(args, stdin, stdout, stderr):
    stdout.write("Commands: " + " ".join(sorted(BUILTINS)) + "\n")
    return 0


BUILTINS = {
    "pwd": cmd_pwd,
    "echo": cmd_echo,
    "cd": cmd_cd,
    "help": cmd_help,
    "env": cmd_env,
}

# File and directory commands: ls mkdir rmdir touch cp mv rm cat chmod
from shell.fileops import FILE_COMMANDS      # Member 1

BUILTINS.update(FILE_COMMANDS)

# Commands from other members (stubs now, real versions later):
from shell.search import cmd_grep            # Member 4
from sched.command import cmd_sched          # Member 2
from deadlock.command import cmd_deadlock    # Member 3

BUILTINS["grep"] = cmd_grep
BUILTINS["sched"] = cmd_sched
BUILTINS["deadlock"] = cmd_deadlock
