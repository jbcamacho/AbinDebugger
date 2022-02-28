"""
Given an integer, this benchmark calculates the factorial of it.
:param sales_today: An integer.
:type  sales_today: int
:rtype: int

"benchmark_metadata": {[
    {
        "Function": ['factorial'],
        "Bug": [('', '')],
        "Fix": [('', '')]
    }
]}
"""
def factorial(x):
    """Recursive function to calculate the 
    factorial of an integer"""
    if x < 0:
        return None
    elif x == 1 or x == 0:
        return 1
    else:
        return (x * factorial(x-1))

print(factorial(3))