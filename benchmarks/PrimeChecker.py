"""
Given an integer, this benchmark check whether it is a prime number or not.
:param s: An integer.
:type  s: int
:rtype: bool

{
    "benchmark_name": "PrimeChecker",
    "benchmark_metadata": [
        {
            "Function": ["PrimeChecker1"],
            "Bug": [ {"Position": 39, "LOC": "if a >= 1:"} ],
            "Fix": [ {"Position": 39, "LOC": "if a > 1:"} ]
        },
        {
            "Function": ["PrimeChecker2"],
            "Bug": [ {"Position": 59, "LOC": "return True"} ],
            "Fix": [ {"Position": 59, "LOC": "return False"} ]
        },
        {
            "Function": ["PrimeChecker3"],
            "Bug": [
                {"Position": 62, "LOC": "if a >= 1:"},
                {"Position": 69, "LOC": "return True"}
            ],
            "Fix": [
                {"Position": 62, "LOC": "if a > 1:"},
                {"Position": 69, "LOC": "return False"}
            ]
        }
    ]
}

The content of this file can be found in JavaTpoint.
@misc{JavaTpoint,
	author = {JavaTpoint},
	title = {{Python Check Prime Number - javatpoint}},
	url = {https://www.javatpoint.com/python-check-prime-number},
}
"""
def PrimeChecker1(a) -> bool:   
    if a >= 1:  # <---- FIX  if a > 1:
        for j in range(2, int(a/2) + 1):  
            if (a % j) == 0:  
                return False  
        else:  
            return True
    else:  
        return False

def PrimeChecker2(a) -> bool:   
    if a > 1:
        for j in range(2, int(a/2) + 1):  
            if (a % j) == 0:  
                return False  
        else:  
            return True
    else:  
        return True # <---- FIX return False

def PrimeChecker3(a) -> bool:   
    if a >= 1:  # <---- FIX if a > 1:
        for j in range(2, int(a/2) + 1):  
            if (a % j) == 0:  
                return False  
        else:  
            return True
    else:  
        return True # <---- FIX return False