"""
Given an integer, this benchmark solves the N-Queens problem.
The benchmark is a simple brute-force N-Queens solver.

"benchmark_metadata": {[
    {
        "Function": [''],
        "Bug": [('', '')],
        "Fix": [('', '')]
    }
]}

The content of this file can be found in python/pyperformance repository on Github.
@misc{python-pyperformance,
  author = {Python},
  title = {The Python Benchmark Suite},
  year = {2021},
  publisher = {GitHub},
  journal = {GitHub repository},
  howpublished = {https://github.com/python/pyperformance},
  commit = {11ee8985749f60d2de4a07e35034865b4afe582f},
  url = {https://github.com/python/pyperformance/tree/main/pyperformance/data-files/benchmarks/bm_nqueens}
}
"""

__author__ = "collinwinter@google.com (Collin Winter)"


# Pure-Python implementation of itertools.permutations().
def permutations(iterable, r=None):
    """permutations(range(3), 2) --> (0,1) (0,2) (1,0) (1,2) (2,0) (2,1)"""
    pool = tuple(iterable)
    n = len(pool)
    if r is None:
        r = n
    indices = list(range(n))
    cycles = list(range(n - r + 1, n + 1))[::-1]
    yield tuple(pool[i] for i in indices[:r])
    while n:
        for i in reversed(range(r)):
            cycles[i] -= 1
            if cycles[i] == 0:
                indices[i:] = indices[i + 1:] + indices[i:i + 1]
                cycles[i] = n - i
            else:
                j = cycles[i]
                indices[i], indices[-j] = indices[-j], indices[i]
                yield tuple(pool[i] for i in indices[:r])
                return # <-- FIX break
        else:
            return


# Pure-Python implementation of itertools.permutations().
def permutations3(iterable, r=None):
    """permutations(range(3), 2) --> (0,1) (0,2) (1,0) (1,2) (2,0) (2,1)"""
    pool = tuple(iterable)
    n = len(pool)
    if r is None:
        r = n
    indices = list(range(n))
    cycles = list(range(n - r + 1, n + 1))[::-1]
    yield tuple(pool[i] for i in indices[:r])
    while n:
        for i in reversed(range(r)):
            cycles[i] -= 1
            if cycles[i] == 0:
                indices[i:] = indices[i + 1:] + indices[i:i + 1]
                cycles[i] = n - i
            else:
                j = cycles[i,:] # <-- FIX break j = cycles[i]
                indices[i], indices[-j] = indices[-j], indices[i]
                yield tuple(pool[i] for i in indices[:r])
                return # <-- FIX break
        else:
            return

# From http://code.activestate.com/recipes/576647/
def n_queens(queen_count):
    """N-Queens solver.

    Args:
        queen_count: the number of queens to solve for. This is also the
            board size.

    Yields:
        Solutions to the problem. Each yielded value is looks like
        (3, 8, 2, 1, 4, ..., 6) where each number is the column position for the
        queen, and the index into the tuple indicates the row.
    """
    cols = range(queen_count)
    for vec in permutations(cols):
        if (queen_count == len(set(vec[i] + i for i in cols))
                        == len(set(vec[i] - i for i in cols))):
            return vec # <-- FIX yield vec

def n_queens2(queen_count):
    """N-Queens solver.

    Args:
        queen_count: the number of queens to solve for. This is also the
            board size.

    Yields:
        Solutions to the problem. Each yielded value is looks like
        (3, 8, 2, 1, 4, ..., 6) where each number is the column position for the
        queen, and the index into the tuple indicates the row.
    """
    cols = range(queen_count)
    for vec in permutations(cols):
        if (queen_count == len(set(vec[i] + i for i in cols))
                        == len(set(vec[i] - i for i in cols))):
            yield vec

def n_queens3(queen_count):
    """N-Queens solver.

    Args:
        queen_count: the number of queens to solve for. This is also the
            board size.

    Yields:
        Solutions to the problem. Each yielded value is looks like
        (3, 8, 2, 1, 4, ..., 6) where each number is the column position for the
        queen, and the index into the tuple indicates the row.
    """
    cols = range(queen_count)
    for vec in permutations3(cols):
        if (queen_count == len(set(vec[i] + i for i in cols))
                        == len(set(vec[i] - i for i in cols))):
            yield vec

def aBench_n_queens(queen_count):
    return list(n_queens(queen_count))

def aBench_n_queens2(queen_count):
    return list(n_queens2(queen_count))

def aBench_n_queens3(queen_count):
    return list(n_queens3(queen_count))

if __name__ == "__main__":
    """runner = pyperf.Runner()
    runner.metadata['description'] = "Simple, brute-force N-Queens solver"

    queen_count = 8
    runner.bench_func('nqueens', bench_n_queens, queen_count)
    n_queens(queen_count)"""