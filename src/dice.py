import re
import random
import itertools


def roll_ndm(n, m, critical_rerolls=False):
    out = []
    i = 0
    while i < n:
        out.append(random.randint(1, m))
        if not critical_rerolls or not out[-1] == m:
            i += 1
    return sorted(out, reverse=True)


def format_roll_result(v, m):
    if v == 1:
        return "**~~1~~**"
    elif v == m:
        return f"**{m}**"
    else:
        return str(v)


def format_roll_ndm_sum(n, m):
    l = roll_ndm(n, m, False)
    r_s = ", ".join([format_roll_result(i, m) for i in l])
    return f"[{n}d{m}: {r_s}] {sum(l)}"


def format_roll_ndm_successes(n, m):
    l = roll_ndm(n, m, True)

    r_s = ", ".join([format_roll_result(i, m) for i in l])
    botches = l.count(1)

    freq = [0] * m
    for i in l:
        freq[m - i] += 1

    ps = list(itertools.accumulate(freq))
    s = [f"vs {i}: {ps[m-i]-botches}" for i in range(m, int(m / 2), -1)]
    s = ", ".join(s)

    return f"[{n}d{m}: {r_s}]\n**Botches:** {botches}\n**Successes:** {s}"


def roll(command):
    command = re.sub(r"(?<!\[) (?![\w\s]*[\]])", "", command)
    command = re.sub(
        r"(?<!\[)(\d+)d(\d+)(?![\w\s]*[\]])",
        lambda m: format_roll_ndm_sum(int(m.group(1)), int(m.group(2))),
        command,
    )
    to_compute = re.sub(r"\[[^\[\]]*\]", "", command)
    command = re.sub(
        r"(?<!\[)[+-](?![\w\s]*[\]])", lambda m: f" {m.group(0)} ", command
    )

    res = eval(to_compute)

    return f"{command}\n**Result:** {res}"
