"""System-file parser.  OWNER: Member 3 (Resources Lead).

File format (see samples/system_safe.txt), '#' starts a comment:
    n_processes n_resources
    <Allocation matrix: n rows>
    <Max matrix: n rows>
    <Available vector: 1 row>
"""


def load_system(path):
    """Return (allocation, maximum, available) as lists of lists of ints.
    Raise ValueError with a clear message on bad dimensions."""
    raise NotImplementedError("load_system")
