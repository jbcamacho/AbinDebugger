"""
From: https://www.javatpoint.com/python-check-prime-number
"""
def PrimeChecker1(a) -> bool:   
    if a >= 1:  # <----  if a > 1:
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
        return True # <----  return False

def PrimeChecker3(a) -> bool:   
    if a >= 1:  # <----  if a > 1:
        for j in range(2, int(a/2) + 1):  
            if (a % j) == 0:  
                return False  
        else:  
            return True
    else:  
        return True # <----  return False