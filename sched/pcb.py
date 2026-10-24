"""PCB and process-file loader.  OWNER: Member 2 (Scheduler Lead).

File format (see samples/processes_basic.txt): one line per process
    PID  arrival  burst  priority        ('#' starts a comment)
"""
from dataclasses import dataclass

NEW, READY, RUNNING, WAITING, TERMINATED = "New", "Ready", "Running", "Waiting", "Terminated"


@dataclass
class PCB:
    pid: str
    arrival: int
    burst: int
    priority: int
    state: str = NEW
    remaining: int = 0
    start: int = -1
    completion: int = 0

    def __post_init__(self):
        self.remaining = self.burst

    @property
    def turnaround(self):
        return self.completion - self.arrival

    @property
    def waiting(self):
        return self.turnaround - self.burst


def load_processes(path):
    """Return a list of PCB. Raise ValueError with a clear message on bad lines."""
    procs = []
    with open(path) as f:
        for n, line in enumerate(f, 1):
            line = line.split("#")[0].strip()
            if not line:
                continue
            parts = line.split()
            if len(parts) != 4:
                raise ValueError(f"{path}:{n}: expected 'PID arrival burst priority'")
            pid, arr, bur, pri = parts
            procs.append(PCB(pid, int(arr), int(bur), int(pri)))
    return procs
