"Configuration handling for the weather project."

DEFAULTS = dict(units='imperial', lang='en')


def load_cfg(path):
    "Read a cfg file from `path`, merging entries over `DEFAULTS`"
    # FIXME: drop this
    cfg = dict(DEFAULTS)
    for line in open(path).read().splitlines():
        k, v = line.split('=', 1)
        cfg[k.strip()] = v.strip()
    return cfg
