"""
Given an integer, this benchmark check whether it is a happy number or not.
A number is said to be happy if it yields 1 when replaced by the sum of squares of its digits repeatedly.
If this process results in an endless cycle of numbers containing 4, then the number will be an unhappy number.
:param s: An integer.
:type  s: int
:rtype: bool

{
    "benchmark_name": "HappyNumber",
    "benchmark_metadata": [
        {
            "Function": ["checkHappyNumber1", "isHappyNumber1"],
            "Bug": [ {"Position": 50, "LOC": "num = num/10"} ],
            "Fix": [ {"Position": 50, "LOC": "num = num//10"} ]
        },
        {
            "Function": ["checkHappyNumber2", "isHappyNumber2"],
            "Bug": [ {"Position": 69, "LOC": "while{num > 1}:"} ],
            "Fix": [ {"Position": 69, "LOC": "while{num > 0}:"} ]
        },
        {
            "Function": ["checkHappyNumber3", "isHappyNumber3"],
            "Bug": [
                {"Position": 91, "LOC": "while{num > 1}:"},
                {"Position": 99, "LOC": "while{result != 1 and result == 4}:"}
            ],
            "Fix": [
                {"Position": 91, "LOC": "while{num > 0}:"},
                {"Position": 99, "LOC": "while{result != 1 and result != 4}:"}
            ]
        }
    ]
}

The content of this file can be found in JavaTpoint.
@misc{JavaTpoint,
	author = {JavaTpoint},
	title = {{Python Check Prime Number - javatpoint}},
	url = {https://www.javatpoint.com/python-program-to-check-if-the-given-number-is-happy-number},
}
"""
def isHappyNumber1(num):    
    rem = sum = 0    
        
    #Calculates the sum of squares of digits    
    while(num > 0):    
        rem = num%10    
        sum = sum + (rem*rem) 
        num = num/10   #<-- FIX num = num//10 
    return sum 
        
def checkHappyNumber1(num):
  result = num
  while(result != 1 and result != 4):    
      result = isHappyNumber1(result)    
      
  #Happy number always ends with 1    
  if(result == 1):    
      return 1
  #Unhappy number ends in a cycle of repeating numbers which contain 4    
  elif(result == 4):    
      return 0

def isHappyNumber2(num):    
    rem = sum = 0    
        
    #Calculates the sum of squares of digits    
    while(num > 1):    #<--- FIX while(num > 0):
        rem = num%10    
        sum = sum + (rem*rem) 
        num = num//10   
    return sum 
        
def checkHappyNumber2(num):
  result = num
  while(result != 1 and result != 4):    
      result = isHappyNumber2(result)    
      
  #Happy number always ends with 1    
  if(result == 1):    
      return 1
  #Unhappy number ends in a cycle of repeating numbers which contain 4    
  elif(result == 4):    
      return 0

def isHappyNumber3(num):    
    rem = sum = 0    
        
    #Calculates the sum of squares of digits    
    while(num > 0):
        rem = num%10    
        sum = sum + (rem*rem) 
        num = num//10   
    return sum 
        
def checkHappyNumber3(num):
  result = num
  while(result != 1 and result == 4):   #<--- FIX while(result != 1 and result != 4):
      result = isHappyNumber3(result)    
      
  #Happy number always ends with 1    
  if(result == 1):    
      return 1
  #Unhappy number ends in a cycle of repeating numbers which contain 4    
  elif(result == 4):    
      return 0
