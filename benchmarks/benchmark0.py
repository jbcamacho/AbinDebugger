def get_profit(sales_today: dict, sales_yesterday: dict) -> int:
    accom: int = 0
    for cost in sales_yesterday.values():
        accom += cost
    for cost in sales_today:
        accom += cost
    return accom