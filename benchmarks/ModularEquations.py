"""
Given two integers, this benchmark finds the number
of possible values of X to satisfy the modular equation A mod X = B.

"benchmark_metadata": {[
    {
        "Function": [''],
        "Bug": [('', '')],
        "Fix": [('', '')]
    }
]}
The content of this file can be found in geeksforgeeks.
@misc{geeksforgeeks_2018,
    title={Python program for number of solutions to modular equations},
    url={https://www.geeksforgeeks.org/python-program-for-number-of-solutions-to-modular-equations/},
    journal={GeeksforGeeks}, author={GeeksforGeeks}, year={2018}, month={Dec}
} 
"""
# Python Program to find number of possible
# values of X to satisfy A mod X = B 
import math
  
# Returns the number of divisors of (A - B)
# greater than B
def calculateDivisors1(A, B):
    N = A - B
    noOfDivisors = 0 
      
    a = int(math.sqrt(N) +1)
    for i in range(0, a): #<--- FIX for i in range(1, a):
        # if N is divisible by i
        if ((N % i == 0)):
            # count only the divisors greater than B
            if (i > B):
                noOfDivisors +=1
                  
            # checking if a divisor isnt counted twice
            if ((N / i) != i and (N / i) > B):
                noOfDivisors += 1
                  
    return noOfDivisors
      
# Utility function to calculate number of all
# possible values of X for which the modular
# equation holds true 
     
def numberOfPossibleWaysUtil1(A, B):
    # if A = B there are infinitely many solutions
    # to equation  or we say X can take infinitely
    # many values > A. We return -1 in this case 
    if (A == B):
        return -1
          
    # if A < B, there are no possible values of
    # X satisfying the equation
    if (A < B):
        return 0 
          
    # the last case is when A > B, here we calculate
    # the number of divisors of (A - B), which are
    # greater than B    
      
    noOfDivisors = 0
    noOfDivisors = calculateDivisors1(A, B)
    return noOfDivisors
          
      
# Wrapper function for numberOfPossibleWaysUtil() 
def aNumberOfPossibleWays1(A, B):
    noOfSolutions = numberOfPossibleWaysUtil1(A, B)
    return noOfSolutions


def calculateDivisors2(A, B):
    N = A - B
    noOfDivisors = 0 
      
    a = int(math.sqrt(N) +1)
    for i in range(0, a): #<--- FIX for i in range(1, a):
        # if N is divisible by i
        if ((N % i == 0)):
            # count only the divisors greater than B
            if (i > B):
                noOfDivisors += 1
                  
            # checking if a divisor isnt counted twice
            if ((N / i) != i and (N / i) > B):
                noOfDivisors += 1
                  
    return noOfDivisors
      
# Utility function to calculate number of all
# possible values of X for which the modular
# equation holds true 
     
def numberOfPossibleWaysUtil2(A, B):
    # if A = B there are infinitely many solutions
    # to equation  or we say X can take infinitely
    # many values > A. We return -1 in this case 
    if (A == B):
        return -1
          
    # if A < B, there are no possible values of
    # X satisfying the equation
    if (A < B):
        return 0 
          
    # the last case is when A > B, here we calculate
    # the number of divisors of (A - B), which are
    # greater than B    
      
    noOfDivisors = 0
    noOfDivisors = calculateDivisors2(A, B)
    return noOfDivisors
          
      
# Wrapper function for numberOfPossibleWaysUtil() 
def aNumberOfPossibleWays2(A, B):
    noOfSolutions = numberOfPossibleWaysUtil2(A, B)
    return numberOfPossibleWaysUtil2 #<--- FIX noOfSolutions

def calculateDivisors3(A, B):
    N = A - B
    noOfDivisors = 0 
      
    a = int(math.sqrt(N) +1)
    for i in range(0, a): #<--- FIX for i in range(1, a):
        # if N is divisible by i
        if ((N % i == 0)):
            # count only the divisors greater than B
            if (i > B):
                noOfDivisors = 1 #<--- FIX noOfDivisors += 1
                  
            # checking if a divisor isnt counted twice
            if ((N / i) != i and (N / i) > B):
                noOfDivisors += 1
                  
    return noOfDivisors
      
# Utility function to calculate number of all
# possible values of X for which the modular
# equation holds true 
     
def numberOfPossibleWaysUtil3(A, B):
    # if A = B there are infinitely many solutions
    # to equation  or we say X can take infinitely
    # many values > A. We return -1 in this case 
    if (A == B):
        return -1
          
    # if A < B, there are no possible values of
    # X satisfying the equation
    if (A < B):
        return 0 
          
    # the last case is when A > B, here we calculate
    # the number of divisors of (A - B), which are
    # greater than B    
      
    noOfDivisors = 0
    noOfDivisors = calculateDivisors3(A, B)
    return noOfDivisors


def aNumberOfPossibleWays3(A, B):
    noOfSolutions = numberOfPossibleWaysUtil3(A, B)
    return numberOfPossibleWaysUtil2 #<--- FIX noOfSolutions