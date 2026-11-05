"""The six scheduling algorithms.  OWNER: Member 2.

Every algorithm has the same shape:
    def fcfs(procs, **opts) -> list of (pid, start, end) segments
Idle CPU time is a segment with pid "IDLE".  The input PCBs are not modified;
report.py works out completion, waiting and turnaround from the segments.

Tie-breaking (all algorithms): earlier arrival first, then earlier line in the file.
Preemption at a tick: processes that arrive at time t join their queue before
a process that is preempted at time t, so new arrivals run first.

Libraries that implement scheduling are NOT used; only collections.deque.

Time model: non-preemptive algorithms (FCFS, SJN, Priority) jump from event to
event.  Preemptive algorithms (RR, MLQ, MLFQ) advance one time unit at a time,
which makes preemption at any tick exact and easy to check by hand.
"""
from collections import deque

INF = float("inf")


def _validate(procs):
    """Reject inputs the algorithms cannot schedule."""
    seen = set()
    for p in procs:
        if p.burst < 1:
            raise ValueError(f"process {p.pid}: burst time must be at least 1")
        if p.pid in seen:
            raise ValueError(f"duplicate PID {p.pid}")
        seen.add(p.pid)


def _arrival_order(procs):
    """Indexes sorted by arrival time, then by input order."""
    return sorted(range(len(procs)), key=lambda i: (procs[i].arrival, i))


def _ticks_to_segments(ticks):
    """Turn one label per time unit into (label, start, end) segments."""
    segs = []
    for t, label in enumerate(ticks):
        if segs and segs[-1][0] == label:
            segs[-1] = (label, segs[-1][1], t + 1)
        else:
            segs.append((label, t, t + 1))
    return segs


def _run_nonpreemptive(procs, key):
    """Run a process to completion; when the CPU is free, pick the ready
    process with the smallest key(i).  Idle gaps become IDLE segments."""
    segs = []
    pending = set(range(len(procs)))
    t = 0
    while pending:
        ready = [i for i in pending if procs[i].arrival <= t]
        if not ready:
            nxt = min(procs[i].arrival for i in pending)
            segs.append(("IDLE", t, nxt))
            t = nxt
            continue
        i = min(ready, key=key)
        segs.append((procs[i].pid, t, t + procs[i].burst))
        t += procs[i].burst
        pending.remove(i)
    return segs


def _multilevel(procs, level_of, quanta, demote):
    """Shared engine for RR, MLQ and MLFQ, one time unit per step.

    level_of(i)  -> starting queue for process i (0 is the highest level)
    quanta[k]    -> time slice for queue k (INF means run until done)
    demote       -> True: a process that uses its whole slice moves one queue down
                    (MLFQ).  False: it goes to the back of its own queue.

    A process in a higher queue always preempts the running process.
    Within a queue, the first process in line runs.
    """
    n = len(procs)
    levels = len(quanta)
    level = [level_of(i) for i in range(n)]      # current queue of each process
    remaining = [p.burst for p in procs]
    queues = [deque() for _ in range(levels)]
    order = _arrival_order(procs)
    next_arrival = 0
    t = 0
    ticks = []
    running = None
    used = 0          # time units the running process has used in this slice
    done = 0

    while done < n:
        # 1. Admit everyone who has arrived by now.
        while next_arrival < n and procs[order[next_arrival]].arrival <= t:
            i = order[next_arrival]
            queues[level[i]].append(i)
            next_arrival += 1

        # 2. Decide whether the running process gives up the CPU.
        if running is not None:
            lv = level[running]
            if any(queues[k] for k in range(lv)):
                # A higher queue has work: preempt, stay in the same queue.
                queues[lv].append(running)
                running = None
            elif used >= quanta[lv]:
                # The slice is used up.
                if demote and lv < levels - 1:
                    level[running] = lv + 1
                    queues[lv + 1].append(running)
                    running = None
                elif queues[lv]:
                    queues[lv].append(running)
                    running = None
                else:
                    used = 0   # nobody else waiting: start a new slice

        # 3. If the CPU is free, take the first process from the highest queue.
        if running is None:
            for lv in range(levels):
                if queues[lv]:
                    running = queues[lv].popleft()
                    used = 0
                    break

        # 4. Run one time unit (or sit idle).
        if running is None:
            ticks.append("IDLE")
            t += 1
            continue
        ticks.append(procs[running].pid)
        remaining[running] -= 1
        used += 1
        t += 1
        if remaining[running] == 0:
            done += 1
            running = None

    return _ticks_to_segments(ticks)


def fcfs(procs, **opts):
    """First come, first served (non-preemptive)."""
    _validate(procs)
    return _run_nonpreemptive(procs, key=lambda i: (procs[i].arrival, i))


def sjn(procs, **opts):
    """Shortest job next (non-preemptive): shortest burst among ready processes."""
    _validate(procs)
    return _run_nonpreemptive(
        procs, key=lambda i: (procs[i].burst, procs[i].arrival, i))


def priority(procs, **opts):
    """Priority scheduling (non-preemptive). Lower number = more important."""
    _validate(procs)
    return _run_nonpreemptive(
        procs, key=lambda i: (procs[i].priority, procs[i].arrival, i))


def rr(procs, quantum=4, **opts):
    """Round-robin with the given time quantum (preemptive, one queue)."""
    _validate(procs)
    if quantum < 1:
        raise ValueError("quantum must be at least 1")
    return _multilevel(procs, lambda i: 0, [quantum], demote=False)


def mlq(procs, quantum=4, **opts):
    """Multilevel queue, three fixed queues chosen by priority number:
        queue 0 (system):      priority 1-2   round-robin, quantum
        queue 1 (interactive): priority 3-4   round-robin, quantum
        queue 2 (batch):       priority 5+    first come, first served
    Higher queues always run first and preempt lower ones.  A process
    stays in its queue for its whole life."""
    _validate(procs)
    if quantum < 1:
        raise ValueError("quantum must be at least 1")

    def level(i):
        pri = procs[i].priority
        if pri <= 2:
            return 0
        if pri <= 4:
            return 1
        return 2

    return _multilevel(procs, level, [quantum, quantum, INF], demote=False)


def mlfq(procs, quantum=2, **opts):
    """Multilevel feedback queue, three levels.  Every process starts in the
    top queue.  Time slices are quantum, 2*quantum and 4*quantum.  A process
    that uses its whole slice drops one level; the bottom level is round-robin.
    Higher levels preempt lower ones.  Priority numbers are ignored here, and
    there is no aging, so a process can wait a long time under heavy load."""
    _validate(procs)
    if quantum < 1:
        raise ValueError("quantum must be at least 1")
    return _multilevel(procs, lambda i: 0,
                       [quantum, 2 * quantum, 4 * quantum], demote=True)


ALGORITHMS = {"fcfs": fcfs, "sjn": sjn, "priority": priority,
              "rr": rr, "mlq": mlq, "mlfq": mlfq}