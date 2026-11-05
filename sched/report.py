"""Shared Gantt chart + table printer.  OWNER: Member 2.

print_report(name, procs, segments, stdout) prints:
  - a text Gantt chart with time marks underneath
  - a table: PID  Arrival  Burst  Completion  Waiting  Turnaround
  - the average waiting and average turnaround time
Turnaround = Completion - Arrival ; Waiting = Turnaround - Burst
Completion is the end time of the last segment of each process.
The PCBs are not changed.
"""


def print_report(name, procs, segments, stdout):
    stdout.write(f"=== {name} ===\n")
    if not procs:
        stdout.write("(no processes)\n")
        return

    # When does each process finish? Its last segment ends at that time.
    completion = {}
    for pid, start, end in segments:
        if pid != "IDLE":
            completion[pid] = max(completion.get(pid, 0), end)

    # ---- Gantt chart ----
    # Each time unit is W characters wide. W is wide enough for the longest label.
    longest = max(len(label) for label, _, _ in segments) if segments else 1
    W = max(4, longest + 2)

    bar = ""                 # the chart line
    col_of_time = []         # (time, column) for every segment boundary
    col = 0
    for label, start, end in segments:
        width = (end - start) * W
        col_of_time.append((start, col))
        bar += "|" + label.center(width - 1)
        col += width
    col_of_time.append((segments[-1][2], col))
    bar += "|"

    # Time marks go underneath, starting at each boundary's column.
    marks = [" "] * (col + 10)
    for t, c in col_of_time:
        for k, ch in enumerate(str(t)):
            marks[c + k] = ch

    stdout.write("\nGantt chart:\n")
    stdout.write(bar + "\n")
    stdout.write("".join(marks).rstrip() + "\n")

    # ---- Table ----
    stdout.write("\n")
    stdout.write(f"{'PID':<6}{'Arrival':>9}{'Burst':>8}"
                 f"{'Completion':>12}{'Waiting':>9}{'Turnaround':>12}\n")
    total_wait = 0
    total_turn = 0
    for p in procs:
        comp = completion.get(p.pid, 0)
        turn = comp - p.arrival
        wait = turn - p.burst
        total_wait += wait
        total_turn += turn
        stdout.write(f"{p.pid:<6}{p.arrival:>9}{p.burst:>8}"
                     f"{comp:>12}{wait:>9}{turn:>12}\n")

    # ---- Averages ----
    n = len(procs)
    stdout.write(f"\nAverage waiting time:    {total_wait / n:.2f}\n")
    stdout.write(f"Average turnaround time: {total_turn / n:.2f}\n")