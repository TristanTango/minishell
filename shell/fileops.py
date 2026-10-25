"""File and directory built-ins.  OWNER: Member 1 (Shell Lead).

ls [-l] [-a] [PATH...]      mkdir [-p] DIR...        rmdir DIR...
touch FILE...               cat [FILE...]            cp [-r] SRC... DEST
mv SRC... DEST              rm [-r] [-f] PATH...     chmod MODE FILE...

All commands follow the shell contract: (args, stdin, stdout, stderr) -> exit code,
never print(), never sys.exit(). No external programs and no shutil are used.

Permissions: on Linux/macOS `chmod` changes the real file mode. Windows has no Unix
permission bits, so there `chmod` records the mode inside the shell (STATE["modes"])
and `ls -l` shows it. Simulated modes last only for the current shell session.
"""
import errno
import os
import re
import stat
import time

from shell.state import STATE

CHUNK = 64 * 1024
MODE_RE = re.compile(r"^[0-7]{3,4}$")
SIMULATE_MODES = os.name == "nt"        # True on Windows (tests can patch this)

_MESSAGES = {
    errno.ENOENT: "No such file or directory",
    errno.EEXIST: "File exists",
    errno.ENOTEMPTY: "Directory not empty",
    errno.EISDIR: "Is a directory",
    errno.ENOTDIR: "Not a directory",
    errno.EACCES: "Permission denied",
    errno.EPERM: "Operation not permitted",
}


def _why(e):
    """Same wording on every operating system."""
    return _MESSAGES.get(e.errno) or e.strerror or str(e)


def _parse_flags(name, args, allowed, stderr):
    """Split args into (flags, operands). Prints an error and returns None if invalid.
    Supports combined flags (-rf), -R as -r, and -- to end the options."""
    flags, operands = set(), []
    options_open = True
    for a in args:
        if options_open and a == "--":
            options_open = False
        elif options_open and a.startswith("-") and len(a) > 1:
            for ch in a[1:]:
                if ch == "R" and "r" in allowed:
                    ch = "r"
                if ch not in allowed:
                    stderr.write(f"{name}: invalid option -- '{ch}'\n")
                    return None
                flags.add(ch)
        else:
            operands.append(a)
    return flags, operands


def _key(path):
    return os.path.normcase(os.path.abspath(path))


# ---------------------------------------------------------------- ls

def _mode_string(path, st):
    if SIMULATE_MODES:
        kind = stat.S_IFDIR if stat.S_ISDIR(st.st_mode) else stat.S_IFREG
        default = 0o755 if kind == stat.S_IFDIR else 0o644
        return stat.filemode(kind | STATE["modes"].get(_key(path), default))
    return stat.filemode(st.st_mode)


def _ls_line(path, name, long_format):
    if not long_format:
        return name
    try:
        st = os.stat(path)
    except OSError:
        return f"?????????? {name}"
    when = time.strftime("%Y-%m-%d %H:%M", time.localtime(st.st_mtime))
    return f"{_mode_string(path, st)} {st.st_size:>8} {when} {name}"


def cmd_ls(args, stdin, stdout, stderr):
    parsed = _parse_flags("ls", args, "la", stderr)
    if parsed is None:
        return 1
    flags, paths = parsed
    long_format, show_all = "l" in flags, "a" in flags
    status = 0
    files, dirs = [], []
    for p in paths or ["."]:
        if not os.path.exists(p):
            stderr.write(f"ls: cannot access '{p}': No such file or directory\n")
            status = 1
        elif os.path.isdir(p):
            dirs.append(p)
        else:
            files.append(p)

    for p in files:
        stdout.write(_ls_line(p, p, long_format) + "\n")
    for n, d in enumerate(dirs):
        if len(paths) > 1:                      # several arguments: label each directory
            if n > 0 or files:
                stdout.write("\n")
            stdout.write(f"{d}:\n")
        try:
            names = os.listdir(d)
        except OSError as e:
            stderr.write(f"ls: cannot open directory '{d}': {_why(e)}\n")
            status = 1
            continue
        if not show_all:
            names = [x for x in names if not x.startswith(".")]
        names.sort(key=lambda s: (s.lower(), s))
        if show_all:
            names = [".", ".."] + names
        for name in names:                      # one per line, so pipes work
            stdout.write(_ls_line(os.path.join(d, name), name, long_format) + "\n")
    return status


# ---------------------------------------------------------------- mkdir, rmdir, touch

def cmd_mkdir(args, stdin, stdout, stderr):
    parsed = _parse_flags("mkdir", args, "p", stderr)
    if parsed is None:
        return 1
    flags, paths = parsed
    if not paths:
        stderr.write("mkdir: missing operand\n")
        return 1
    status = 0
    for p in paths:
        try:
            if "p" in flags:
                os.makedirs(p, exist_ok=True)
            else:
                os.mkdir(p)
        except OSError as e:
            stderr.write(f"mkdir: cannot create directory '{p}': {_why(e)}\n")
            status = 1
    return status


def cmd_rmdir(args, stdin, stdout, stderr):
    parsed = _parse_flags("rmdir", args, "", stderr)
    if parsed is None:
        return 1
    _, paths = parsed
    if not paths:
        stderr.write("rmdir: missing operand\n")
        return 1
    status = 0
    for p in paths:
        if not os.path.lexists(p):
            stderr.write(f"rmdir: failed to remove '{p}': No such file or directory\n")
            status = 1
        elif not os.path.isdir(p):
            stderr.write(f"rmdir: failed to remove '{p}': Not a directory\n")
            status = 1
        else:
            try:
                os.rmdir(p)
            except OSError as e:
                stderr.write(f"rmdir: failed to remove '{p}': {_why(e)}\n")
                status = 1
    return status


def cmd_touch(args, stdin, stdout, stderr):
    parsed = _parse_flags("touch", args, "", stderr)
    if parsed is None:
        return 1
    _, paths = parsed
    if not paths:
        stderr.write("touch: missing file operand\n")
        return 1
    status = 0
    for p in paths:
        try:
            if not os.path.isdir(p):
                with open(p, "a"):          # creates the file if it does not exist
                    pass
            os.utime(p, None)               # update the modification time
        except OSError as e:
            stderr.write(f"touch: cannot touch '{p}': {_why(e)}\n")
            status = 1
    return status


# ---------------------------------------------------------------- cat

def cmd_cat(args, stdin, stdout, stderr):
    status = 0
    for p in args or ["-"]:                 # no files (or "-") means read stdin
        if p == "-":
            stdout.write(stdin.read())
            continue
        try:
            if os.path.isdir(p):
                raise IsADirectoryError(errno.EISDIR, "Is a directory")
            with open(p, encoding="utf-8", errors="replace") as f:
                stdout.write(f.read())
        except OSError as e:
            stderr.write(f"cat: {p}: {_why(e)}\n")
            status = 1
    return status


# ---------------------------------------------------------------- cp, mv, rm

def _copy_file(src, dst):
    with open(src, "rb") as fin, open(dst, "wb") as fout:
        while True:
            chunk = fin.read(CHUNK)
            if not chunk:
                break
            fout.write(chunk)


def _copy_tree(src, dst):
    os.makedirs(dst, exist_ok=True)
    for name in os.listdir(src):
        s, d = os.path.join(src, name), os.path.join(dst, name)
        if os.path.isdir(s):
            _copy_tree(s, d)
        else:
            _copy_file(s, d)


def _remove_tree(path):
    for name in os.listdir(path):
        p = os.path.join(path, name)
        if os.path.isdir(p) and not os.path.islink(p):
            _remove_tree(p)
        else:
            os.remove(p)
    os.rmdir(path)


def _inside(child, parent):
    a, b = os.path.normcase(os.path.abspath(parent)), os.path.normcase(os.path.abspath(child))
    return b == a or b.startswith(a + os.sep)


def _split_sources(name, operands, stderr):
    """Return (sources, dest, dest_is_dir) or None after printing an error."""
    if not operands:
        stderr.write(f"{name}: missing file operand\n")
        return None
    if len(operands) < 2:
        stderr.write(f"{name}: missing destination file operand after '{operands[0]}'\n")
        return None
    *sources, dest = operands
    dest_is_dir = os.path.isdir(dest)
    if len(sources) > 1 and not dest_is_dir:
        stderr.write(f"{name}: target '{dest}' is not a directory\n")
        return None
    return sources, dest, dest_is_dir


def _target(src, dest, dest_is_dir):
    if dest_is_dir:
        return os.path.join(dest, os.path.basename(os.path.normpath(src)))
    return dest


def cmd_cp(args, stdin, stdout, stderr):
    parsed = _parse_flags("cp", args, "r", stderr)
    if parsed is None:
        return 1
    flags, operands = parsed
    split = _split_sources("cp", operands, stderr)
    if split is None:
        return 1
    sources, dest, dest_is_dir = split
    status = 0
    for src in sources:
        target = _target(src, dest, dest_is_dir)
        try:
            if not os.path.exists(src):
                stderr.write(f"cp: cannot stat '{src}': No such file or directory\n")
                status = 1
            elif os.path.isdir(src):
                if "r" not in flags:
                    stderr.write(f"cp: -r not specified; omitting directory '{src}'\n")
                    status = 1
                elif _inside(target, src):
                    stderr.write(f"cp: cannot copy directory '{src}' into itself\n")
                    status = 1
                else:
                    _copy_tree(src, target)
            elif os.path.exists(target) and os.path.samefile(src, target):
                stderr.write(f"cp: '{src}' and '{target}' are the same file\n")
                status = 1
            else:
                _copy_file(src, target)
        except OSError as e:
            stderr.write(f"cp: cannot copy '{src}' to '{target}': {_why(e)}\n")
            status = 1
    return status


def cmd_mv(args, stdin, stdout, stderr):
    parsed = _parse_flags("mv", args, "", stderr)
    if parsed is None:
        return 1
    _, operands = parsed
    split = _split_sources("mv", operands, stderr)
    if split is None:
        return 1
    sources, dest, dest_is_dir = split
    status = 0
    for src in sources:
        target = _target(src, dest, dest_is_dir)
        try:
            if not os.path.lexists(src):
                stderr.write(f"mv: cannot stat '{src}': No such file or directory\n")
                status = 1
            elif os.path.isdir(src) and _inside(target, src):
                stderr.write(f"mv: cannot move '{src}' to a subdirectory of itself\n")
                status = 1
            else:
                try:
                    os.replace(src, target)
                except OSError as e:
                    if e.errno != errno.EXDEV:      # other drive: copy, then delete
                        raise
                    if os.path.isdir(src):
                        _copy_tree(src, target)
                        _remove_tree(src)
                    else:
                        _copy_file(src, target)
                        os.remove(src)
        except OSError as e:
            stderr.write(f"mv: cannot move '{src}' to '{target}': {_why(e)}\n")
            status = 1
    return status


def cmd_rm(args, stdin, stdout, stderr):
    parsed = _parse_flags("rm", args, "rf", stderr)
    if parsed is None:
        return 1
    flags, paths = parsed
    if not paths:
        if "f" in flags:
            return 0
        stderr.write("rm: missing operand\n")
        return 1
    status = 0
    for p in paths:
        if os.path.basename(os.path.normpath(p)) in (".", ".."):
            stderr.write(f"rm: refusing to remove '.' or '..': '{p}'\n")
            status = 1
            continue
        absolute = os.path.abspath(p)
        if os.path.dirname(absolute) == absolute:
            stderr.write("rm: refusing to remove the root directory\n")
            status = 1
            continue
        if not os.path.lexists(p):
            if "f" not in flags:
                stderr.write(f"rm: cannot remove '{p}': No such file or directory\n")
                status = 1
            continue
        try:
            if os.path.isdir(p) and not os.path.islink(p):
                if "r" not in flags:
                    stderr.write(f"rm: cannot remove '{p}': Is a directory\n")
                    status = 1
                    continue
                _remove_tree(p)
            else:
                os.remove(p)
        except OSError as e:
            stderr.write(f"rm: cannot remove '{p}': {_why(e)}\n")
            status = 1
    return status


# ---------------------------------------------------------------- chmod

def cmd_chmod(args, stdin, stdout, stderr):
    if len(args) < 2:
        stderr.write("chmod: usage: chmod MODE FILE...   (example: chmod 755 script.sh)\n")
        return 1
    mode_text, paths = args[0], args[1:]
    if not MODE_RE.match(mode_text):
        stderr.write(f"chmod: invalid mode: '{mode_text}' (use an octal number such as 755)\n")
        return 1
    mode = int(mode_text, 8)
    status = 0
    for p in paths:
        if not os.path.exists(p):
            stderr.write(f"chmod: cannot access '{p}': No such file or directory\n")
            status = 1
            continue
        try:
            if SIMULATE_MODES:
                STATE["modes"][_key(p)] = mode
            else:
                os.chmod(p, mode)
        except OSError as e:
            stderr.write(f"chmod: changing permissions of '{p}': {_why(e)}\n")
            status = 1
    return status


FILE_COMMANDS = {
    "ls": cmd_ls, "mkdir": cmd_mkdir, "rmdir": cmd_rmdir, "touch": cmd_touch,
    "cat": cmd_cat, "cp": cmd_cp, "mv": cmd_mv, "rm": cmd_rm, "chmod": cmd_chmod,
}
