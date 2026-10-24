"""Detection and Banker's algorithm.  OWNER: Member 3.

Need = Max - Allocation.
  detect(alloc, maximum, available)         -> list of deadlocked process indexes ([] if none)
  is_safe(alloc, maximum, available)        -> (True, safe_sequence) or (False, [])
  request(alloc, maximum, available, i, req)-> (granted: bool, reason: str)
Bonus: recovery suggestion (terminate a process / preempt a resource).
Libraries that implement these algorithms are NOT allowed.
"""


def detect(alloc, maximum, available):
    raise NotImplementedError("detect")


def is_safe(alloc, maximum, available):
    raise NotImplementedError("is_safe")


def request(alloc, maximum, available, i, req):
    raise NotImplementedError("request")
