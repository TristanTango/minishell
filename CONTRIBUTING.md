# Team rules

## Command contract (the most important rule)
Every command is `def cmd_name(args, stdin, stdout, stderr) -> int`.
- Output goes through `stdout.write()` / `stderr.write()`. **Never `print()`.**
- Input comes from `stdin`. **Never `input()`.**
- **Never `sys.exit()`.** Return an exit code (0 = success).
- Never let an exception escape. Print a clear error and return nonzero.

This is what makes redirection and pipes work for every command.

## Git workflow
- `main` always runs. Work on a branch: `member1/redirection`, `member2/rr`, ...
- Open a pull request; **another member reviews before merge**.
- Commit small and often with clear messages. Everyone needs real commits (they affect grades).

## Rules from the assignment
- All code written by the group. Standard library only; only `re`/basic I/O may be used for
  the algorithms area (no library that implements scheduling or deadlock algorithms).
- Do NOT call real `ls`, `grep`, etc. (no `subprocess` for built-ins).
- At least 3 test inputs per simulator, including an edge case.
- Comment your code.

## Meetings
At least once a week. Save notes in `docs/meeting-notes.md`.
