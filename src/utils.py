import math


def split_long_message(s):
    n = 5
    s = s.split("\n")
    out = []
    for i in range(math.ceil(len(s) / n)):
        out.append("\n".join(s[i * n : (i + 1) * n]))
    return out
