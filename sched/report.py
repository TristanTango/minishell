"""Shared Gantt chart + table printer.  OWNER: Member 2.

TODO: print_report(name, procs, segments, stdout)
  - text Gantt chart, e.g.  |P1  |P2|P1 |   with time marks underneath
  - table: PID  Arrival  Burst  Completion  Waiting  Turnaround
  - averages for waiting and turnaround
  Turnaround = Completion - Arrival ; Waiting = Turnaround - Burst
"""


def print_report(name, procs, segments, stdout):
    raise NotImplementedError("print_report")
