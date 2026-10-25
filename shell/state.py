"""Shared shell state, imported by core.py and by built-ins (e.g. env, chmod).

vars        : shell variables set with NAME=value
last_status : exit code of the last command, available as $?
modes       : simulated permission bits per path (used by chmod / ls -l on Windows)
"""
STATE = {"vars": {}, "last_status": 0, "modes": {}}
