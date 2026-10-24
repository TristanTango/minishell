"""The `sched` command.  OWNER: Member 2.

Usage: sched ALGO [--quantum N] FILE      ALGO = fcfs|sjn|priority|rr|mlq|mlfq
       sched compare FILE                 (Module 4: all six on the same input)
"""


def cmd_sched(args, stdin, stdout, stderr):
    # TODO: parse args, load_processes, run algorithm, print_report.
    # Print a clear error for: unknown algorithm, missing file, bad quantum.
    stderr.write("sched: not implemented yet\n")
    return 1
