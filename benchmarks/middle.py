"""
Given three real numbers x, y and z, this benchmark returns the "middle" number of three values.
:param x: A real number.
:type  x: Tuple[int, float]
:param y: A real number.
:type  y: Tuple[int, float]
:param z: A real number.
:type  z: Tuple[int, float]
:rtype: Tuple[int, float]

"benchmark_metadata": {[
    {
        "Function": ['Middle'],
        "Bug": [('Line 35', 'return y')],
        "Fix": [('Line 35', 'return x')]
    }
]}
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
def middle(x, y, z):
    if y < z:
        if x < y:
            return y
        elif x < z:
            return y # <-- FIX return x
    else:
        if x > y:
            return y
        elif x > z:
            return x
    return z