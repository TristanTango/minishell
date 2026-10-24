"""grep-like search command.  OWNER: Member 4 (Docs and Testing Lead).

Usage: grep TEXT [FILE]     (reads stdin if no FILE, so it works in pipes)
Required: print every line containing TEXT.
Bonus: . [a-z] * + ? backslash escaping, capturing groups (the `re` module is allowed).
"""


def cmd_grep(args, stdin, stdout, stderr):
    # TODO: implement. Return 0 if a line matched, 1 if none, 2 on error (like real grep).
    stderr.write("grep: not implemented yet\n")
    return 1
