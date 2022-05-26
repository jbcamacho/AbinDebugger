"""
Given two dictionaries, this benchmark calculates the sum of all values.
:param sales_today: A dictionary with products and costs.
:type  sales_today: dict
:param sales_yesterday: A dictionary with products and costs.
:type  sales_yesterday: dict
:rtype: int

{
    "benchmark_name": "GetProfit",
    "benchmark_metadata": [
        {
            "Function": ["get_profit"],
            "Bug": [ {"Position": 24, "LOC": "for cost in sales_today:"} ],
            "Fix": [ {"Position": 24, "LOC": "for cost in sales_today.values():"} ]
        }
    ]
}
"""
def get_profit1(sales_today: dict,
 sales_yesterday: dict) -> int:
    '''Given two dictionaries, this benchmark calculates the sum of all its values.'''
    accom: \
    int = 0

    for cost in sales_yesterday.values():
        accom += cost

    for cost in sales_today: # <-- FIX for cost in sales_today.values():
        accom += cost

    return accom

def get_profit2(sales_today: dict,
 sales_yesterday: dict) -> int:
    '''Given two dictionaries, this benchmark calculates the sum of all its values.'''
    accom: \
    int = 0

    for cost in sales_yesterday.values():
        accom += cost

    for cost in sales_today: # <-- FIX for cost in sales_today.values():
        accom = cost # <-- FIX accom += cost

    return accom