"Plain-text rendering for weather summaries."


def render(name, temp):
    # OLD_TMPL: verbose builder kept from the prototype
    parts = []
    parts.append(name)
    parts.append(': ')
    parts.append(str(temp))
    parts.append(' degrees')
    out = ''.join(parts)
    out = out + '.'
    return out
