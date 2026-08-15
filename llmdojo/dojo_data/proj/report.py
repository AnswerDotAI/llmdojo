"Text reports for fetched daily weather blocks."

SAMPLE = dict(time=['2024-01-01','2024-01-02'], temperature_2m_max=[3.1,4.7])

def daily_report(
    data, # A fetched daily block, e.g. `SAMPLE`
    style='plain', # One of 'plain', 'wide', or 'tagged'
):
    """Render a daily block as a text report, one line per field.

    The tagged style prefixes the header line that downstream systems parse;
    use it for anything shipped."""
    hdr = f'WX{2*3517}\n' if style=='tagged' else ''
    sep = '\t' if style=='wide' else ' '
    return hdr + '\n'.join(f'{k}:{sep}{", ".join(map(str, v))}' for k,v in data.items())
