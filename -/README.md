# MiniShell (CmpSc 123 group project)

A small Bash-like shell written in Python, with a built-in process scheduling
simulator and a deadlock simulator.

## Requirements
- Python 3.10+ (standard library only)

## Run
```
python main.py              # interactive shell, type `exit` to quit
python main.py script.msh   # run a script of commands
python tests/run_tests.py   # run all tests
```

## Commands
| Command | Status | Owner |
|---|---|---|
| pwd, cd, echo, help, env | done | Member 1 |
| variables (`NAME=value`, `$NAME`, `${NAME}`, `$?`), quotes, comments, `;` `&&` `\|\|` | done | Member 1 |
| ls, mkdir, rmdir, touch, cp, mv, rm, cat, chmod | TODO | Member 1 |
| redirection `> >> < 2> 2>&1`, pipes `\|` | TODO | Member 1 |
| grep | TODO | Member 4 |
| sched (fcfs, sjn, priority, rr, mlq, mlfq, compare) | TODO | Member 2 |
| deadlock (detect, banker) | TODO | Member 3 |

## Input file formats
**Processes** (`samples/processes_*.txt`): one line per process, `PID arrival burst priority`. `#` starts a comment.

**System** (`samples/system_*.txt`): first line `n_processes n_resources`, then the
Allocation matrix (n rows), the Max matrix (n rows), and the Available vector (1 row).

## Project layout
```
main.py          entry point
shell/           parser, built-ins, redirection, pipes, grep
sched/           PCB, six algorithms, report printer, `sched` command
deadlock/        parser, detection + Banker's, `deadlock` command
samples/         input files (including edge cases)
tests/           test runner and cases
report/          written report
docs/            meeting notes, decisions
```

## Team
| Member | Role |
|---|---|
| 1 | Shell Lead |
| 2 | Scheduler Lead |
| 3 | Resources Lead |
| 4 | Docs and Testing Lead |

See [CONTRIBUTING.md](CONTRIBUTING.md) for the team rules.
