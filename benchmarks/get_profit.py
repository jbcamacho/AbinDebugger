"""
Given two dictionaries, this benchmark calculates the sum of all values in them.
:param sales_today: A dictionary with products and costs.
:type  sales_today: dict
:param sales_yesterday: A dictionary with products and costs.
:type  sales_yesterday: dict
:rtype: int

"benchmark_metadata": {[
    {
        "Function": ['get_profit'],
        "Bug": [('Line 21', 'for cost in sales_today:')],
        "Fix": [('Line 21', 'for cost in sales_today.values():')]
    }
]}
"""
def get_profit(sales_today: dict, sales_yesterday: dict) -> int:
    accom: int = 0
    for cost in sales_yesterday.values():
        accom += cost
    for cost in sales_today: # <-- FIX for cost in sales_today.values():
        accom += cost
    return accom