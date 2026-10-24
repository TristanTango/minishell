"""Tokenizer, variable expansion and command-list parser.  OWNER: Member 1.

Pipeline:  line --tokenize--> tokens --parse--> [(connector, tokens), ...]
Expansion ($NAME) happens later, at run time, so `A=1; echo $A` works.

A token is either
    ("word", segments)   segments = [(text, mode), ...], mode in plain|single|double
    ("op", "&&")         one of OPERATORS
Quote rules (like Bash):  'single' = literal,  "double" = $ expands,  a backslash makes the next character literal.
"""
import re

# Longest first so "2>&1" wins over "2>" and "&&" wins over "&".
OPERATORS = ["2>&1", "&&", "||", ">>", "2>", ";", "|", ">", "<"]
CONNECTORS = (";", "&&", "||")
ASSIGN_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*=")
VAR_RE = re.compile(r"\$(\?|[A-Za-z_][A-Za-z0-9_]*|\{[A-Za-z_][A-Za-z0-9_]*\})")


class ParseError(Exception):
    pass


def tokenize(line):
    tokens, segs, buf = [], [], []
    in_word = False
    i, n = 0, len(line)

    def flush_buf():
        if buf:
            segs.append(("".join(buf), "plain"))
            buf.clear()

    def end_word():
        nonlocal segs, in_word
        flush_buf()
        if in_word:
            tokens.append(("word", segs))
        segs, in_word = [], False

    while i < n:
        c = line[i]
        if c in " \t":
            end_word()
            i += 1
        elif c == "#" and not in_word:      # comment: ignore the rest of the line
            break
        elif c in "'\"":
            flush_buf()
            j = line.find(c, i + 1)
            if j == -1:
                raise ParseError("unterminated quote")
            segs.append((line[i + 1:j], "single" if c == "'" else "double"))
            in_word = True
            i = j + 1
        elif c == "\\" and i + 1 < n:       # escaped character is taken literally
            flush_buf()
            segs.append((line[i + 1], "single"))
            in_word = True
            i += 2
        else:
            for op in OPERATORS:
                if line.startswith(op, i):
                    if op[0] == "2" and (in_word or buf):   # "2>" only at word start
                        continue
                    end_word()
                    tokens.append(("op", op))
                    i += len(op)
                    break
            else:
                if c == "&":
                    raise ParseError("'&' (background jobs) is not supported")
                buf.append(c)
                in_word = True
                i += 1
    end_word()
    return tokens


def parse(line):
    """Split a line into [(connector, tokens)].

    connector is None for the first command, otherwise ';', '&&' or '||' (how it
    is joined to the PREVIOUS command). Raises ParseError on bad syntax.
    Pipes and redirections stay inside `tokens` for the executor (TODO Member 1).
    """
    tokens = tokenize(line)
    items, current, connector = [], [], None
    for tok in tokens:
        if tok[0] == "op" and tok[1] in CONNECTORS:
            if not current:
                raise ParseError(f"unexpected '{tok[1]}'")
            items.append((connector, current))
            connector, current = tok[1], []
        else:
            current.append(tok)
    if current:
        items.append((connector, current))
    elif connector in ("&&", "||"):
        raise ParseError(f"missing command after '{connector}'")
    return items            # a trailing ';' is allowed


def expand_word(segs, variables, last_status):
    """Replace $NAME, ${NAME} and $? inside plain/double-quoted segments."""
    def lookup(m):
        name = m.group(1)
        if name == "?":
            return str(last_status)
        if name.startswith("{"):
            name = name[1:-1]
        return variables.get(name, "")

    out = []
    for text, mode in segs:
        out.append(text if mode == "single" else VAR_RE.sub(lookup, text))
    return "".join(out)
