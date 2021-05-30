import re


def split_args_kwargs(l):
    d = {}
    for i in l:
        if re.match("\w+:\w+", i):
            k, v = i.split(":")
            d[k] = v

    return [i for i in l if not re.match("\w+:\w+", i)], d
