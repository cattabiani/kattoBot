import itertools
import random
import re


class Dice:
    def __init__(self, base, reroll_criticals=False):
        self.reroll_criticals = reroll_criticals

        n, m = base.split("d")
        self.n_dice = int(n)
        self.m_faces = int(m)

        self.result = []
        self.successes_per_diff_level = []
        self.freq = []
        self.roll(reroll_criticals)

    def _format_die_result(self, v):
        """ Pretty-print roll result """
        if v == 1:
            return "**~~1~~**"
        elif v == self.m_faces:
            return f"**{v}**"
        else:
            return str(v)

    def __str__(self, base=False, add_sum=True):
        """Print the roll

        Args:
              base: it prints the base line like `3d10`
              add_sum: it appends the sum fo the roll result sum at the end
        """
        if base:
            return f"{self.n_dice}d{self.m_faces}"
        else:
            r_s = ", ".join([self._format_die_result(i) for i in self.result])
            out = f"[{self.__str__(base=True)}: {r_s}]"

            if add_sum:
                out += f" {sum(self.result)}"

            return out

    def roll(self, reroll_criticals=False):
        """Roll dice

        Roll dice and get sorted results. Critical rerolls make the code reroll the die on max result (used in vamps).

        Args:
              n: number of dice to roll
              m: number of faces of a die
              critical_rerolls: flag that decides if we reroll the die on max result (critical)
        """

        self.reroll_criticals = reroll_criticals
        self.result = []
        self.freq = [0] * self.m_faces
        i = 0
        while i < self.n_dice:
            v = random.randint(1, self.m_faces)
            self.result.append(v)
            self.freq[v - 1] += 1
            if not self.reroll_criticals or not self.result[-1] == self.m_faces:
                i += 1

        self.freq.reverse()

        self.successes_per_diff_level = [
            max(self.freq[0], i - self.freq[-1])
            for i in itertools.accumulate(self.freq)
        ]
        self.result = sorted(self.result, reverse=True)


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

        dd = Dice(i, successes)
        m_max = max(m_max, dd.m_faces)
        p[idx] = dd.__str__(base=False, add_sum=(not successes))
        c.append(dd)

    # compute full string
    res = []
    if not successes:
        res = [
            eval("".join([str(sum(i.result)) if isinstance(i, Dice) else i for i in c]))
        ]
    else:
        for i in range(0, int((m_max + 1) / 2)):
            tbc = c.copy()
            for idx, j in enumerate(tbc):
                if not isinstance(j, Dice):
                    continue
                tbc[idx] = str(j.successes_per_diff_level[i])
            res.append(eval("".join(tbc)))

    # n botches
    botches = sum([i.freq[-1] for i in c if isinstance(i, Dice)])

    # formatting
    p = " ".join([i if i.startswith("[") else re.sub(" ", "", i) for i in p if i != ""])
    p = re.sub(r"(?<!\[)[+-](?![\w\s]*[\]])", lambda m: f" {m.group(0)} ", p)
    p = re.sub(" +", " ", p)
    out = f"**Roll:** {p} **Result:** {res[0]}\n"
    if successes:
        out += "**Successes:** " + ", ".join(
            [f"vs {m_max - idx}: {i}" for idx, i in enumerate(res)]
        )
        out += f"\n**Botches:** {botches}"

    return out
