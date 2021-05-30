import re
import random
import itertools


def roll_ndm(n, m, critical_rerolls=False):
    """Roll dice

    Roll dice and get sorted results. Critical rerolls make the code reroll the die on max result (used in vamps).

    Args:
          n: number of dice to roll
          m: number of faces of a die
          critical_rerolls: flag that decides if we reroll the die on max result (critical)
    """
    out = []
    freq = [0] * m
    i = 0
    while i < n:
        v = random.randint(1, m)
        out.append(v)
        freq[v - 1] += 1
        if not critical_rerolls or not out[-1] == m:
            i += 1

    freq.reverse()
    dist = list(itertools.accumulate(freq))

    return sorted(out, reverse=True), dist


def format_roll_result(v, m):
    """ Pretty-print roll result """
    if v == 1:
        return "**~~1~~**"
    elif v == m:
        return f"**{m}**"
    else:
        return str(v)


def roll(s, successes):
    """Main roller

    We get the results from roll_ndm, "add them up" and format results
    """

    # Split in the printing list (p) and the computing list (c) so that stuff in [] is avoided and rolls are isolated
    p = [i for i in re.split("(\[*[^\[\]]*\]|\d+d\d+)", s) if i != ""]
    c = []

    # visit the printing list to compute rolls, create the computing list (c) and get m_max (could be useful for
    # successes)
    m_max = 0
    for idx, i in enumerate(p):
        if re.match("\[*[^\[\]]*\]", i):
            continue
        if not re.match("\d+d\d+", i):
            c.append(i)
            continue
        n, m = i.split("d")
        m = int(m)
        n = int(n)
        m_max = max(m_max, m)
        rolls, dist = roll_ndm(n, m, successes)
        r_s = ", ".join([format_roll_result(i, m) for i in rolls])
        p[idx] = f"[{n}d{m}: {r_s}]"
        if not successes:
            rolls_sum = sum(rolls)
            p[idx] += f" {rolls_sum} "
            c.append(str(rolls_sum))
        else:
            c.append(dist)

    # compute botches and rolls for compute results
    res = []
    botches = sum([i[-1] - i[-2] for i in c if isinstance(i, list)])
    if not successes:
        res = [eval("".join(c))]
    else:
        for i in range(0, int((m_max + 1) / 2)):
            tbc = c.copy()
            for idx, j in enumerate(tbc):
                if not isinstance(j, list):
                    continue
                b = j[-1] - j[-2]
                tbc[idx] = str(j[i] - b)
            res.append(eval("".join(tbc)))

    # formatting
    p = " ".join([i if i.startswith("[") else re.sub(" ", "", i) for i in p if i != ""])
    p = re.sub(r"(?<!\[)[+-](?![\w\s]*[\]])", lambda m: f" {m.group(0)} ", p)
    out = f"**Roll:**\n{p}\n**Result:** "
    if not successes:
        out += f"{res[0]}"
    else:
        out += ", ".join([f"vs {m_max - idx}: {i}" for idx, i in enumerate(res)])
        out += f"\n**Botches:** {botches}"

    return out
