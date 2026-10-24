"""Shared shell state, imported by core.py and by built-ins (e.g. env).

vars        : shell variables set with NAME=value
last_status : exit code of the last command, available as $?
"""
STATE = {"vars": {}, "last_status": 0}
