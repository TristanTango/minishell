"""The `sched` command.  OWNER: Member 2.

Usage: sched ALGO [--quantum N] FILE      ALGO = fcfs|sjn|priority|rr|mlq|mlfq
       sched compare FILE                 (Module 4: all six on the same input)

Returns 0 on success and 1 on error.  Never calls sys.exit.
"""
from sched.pcb import load_processes
from sched.algorithms import ALGORITHMS
from sched.report import print_report

USAGE = "usage: sched ALGO [--quantum N] FILE"
ALGO_NAMES = ", ".join(ALGORITHMS)
# Algorithms that take a quantum, and their defaults (see algorithms.py).
QUANTUM_DEFAULT = {"rr": 4, "mlq": 4, "mlfq": 2}


def cmd_sched(args, stdin, stdout, stderr):
    if args and args[0] == "compare":
        stderr.write("sched compare: not implemented yet (Module 4)\n")
        return 1

    # Split the arguments into --quantum N and the positional ones.
    quantum = None
    positional = []
    i = 0
    while i < len(args):
        if args[i] == "--quantum":
            if i + 1 >= len(args):
                stderr.write("sched: --quantum needs a value\n" + USAGE + "\n")
                return 1
            try:
                quantum = int(args[i + 1])
            except ValueError:
                stderr.write(f"sched: bad quantum '{args[i + 1]}': "
                             "must be a whole number\n")
                return 1
            if quantum < 1:
                stderr.write(f"sched: bad quantum {quantum}: must be at least 1\n")
                return 1
            i += 2
        else:
            positional.append(args[i])
            i += 1

    if len(positional) != 2:
        stderr.write(USAGE + "\n")
        return 1
    algo, path = positional

    if algo not in ALGORITHMS:
        stderr.write(f"sched: unknown algorithm '{algo}' "
                     f"(choose from {ALGO_NAMES})\n")
        return 1

    try:
        procs = load_processes(path)
    except FileNotFoundError:
        stderr.write(f"sched: cannot open '{path}': no such file\n")
        return 1
    except ValueError as e:
        stderr.write(f"sched: {e}\n")
        return 1

    opts = {} if quantum is None else {"quantum": quantum}
    try:
        segments = ALGORITHMS[algo](procs, **opts)
    except ValueError as e:
        stderr.write(f"sched: {e}\n")
        return 1

    title = algo.upper()
    if algo in QUANTUM_DEFAULT:
        shown = quantum if quantum is not None else QUANTUM_DEFAULT[algo]
        title += f" (quantum {shown})"
    print_report(title, procs, segments, stdout)
    return 0