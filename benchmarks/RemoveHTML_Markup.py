"""
Given an HTML string, this benchmark removes HTML markup and converts it into text.
:param s: A HTML string.
:type  s: str
:rtype: str

{
    "benchmark_name": "RemoveHTML_Markup",
    "benchmark_metadata": [
        {
            "Function": ["remove_html_markup"],
            "Bug": [ {"Position": 40, "LOC": "elif c == '\\\"' or c == \\\"'\\\" and tag:"} ],
            "Fix": [ {"Position": 40, "LOC": "elif (c == '\\\"' or c == \\\"'\\\") and tag:"} ]
        }
    ]
}

The content of this file can be found in The Debugging Book.
@book{debuggingbook2021,
    author = {Andreas Zeller},
    title = {The Debugging Book},
    year = {2021},
    publisher = {CISPA Helmholtz Center for Information Security},
    howpublished = {\\url{https://www.debuggingbook.org/}},
    note = {Retrieved 2022-02-02 19:00:00-06:00},
    url = {https://www.debuggingbook.org/},
    urldate = {2021-10-13 13:24:19+02:00}
}
"""
def remove_html_markup(s):
    tag = False
    quote = False
    out = ""

    for c in s:
        if c == '<' and not quote:
            tag = True
        elif c == '>' and not quote:
            tag = False
        elif c == '"' or c == "'" and tag:  # <-- FIX elif (c == '"' or c == "'") and tag:
            quote = not quote
        elif not tag:
            out = out + c
    
    return out