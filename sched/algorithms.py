"""The six scheduling algorithms.  OWNER: Member 2.

Every algorithm has the same shape:
    def fcfs(procs, **opts) -> list of (pid, start, end) segments
The shared printer in report.py turns segments into the Gantt chart, the
waiting/turnaround table and the averages. Use "IDLE" as pid for CPU gaps.
Libraries that implement scheduling are NOT allowed.
"""


def fcfs(procs, **opts):
    raise NotImplementedError("fcfs")


def sjn(procs, **opts):
    raise NotImplementedError("sjn")


def priority(procs, **opts):
    raise NotImplementedError("priority")


def rr(procs, quantum=4, **opts):
    raise NotImplementedError("rr")


def mlq(procs, **opts):
    raise NotImplementedError("mlq")


def mlfq(procs, **opts):
    raise NotImplementedError("mlfq")


ALGORITHMS = {"fcfs": fcfs, "sjn": sjn, "priority": priority,
              "rr": rr, "mlq": mlq, "mlfq": mlfq}
