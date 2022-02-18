"""
A number is said to be happy if it yields 1 when replaced by the sum of squares of its digits repeatedly.
If this process results in an endless cycle of numbers containing 4, then the number will be an unhappy number.
From: https://www.javatpoint.com/python-program-to-check-if-the-given-number-is-happy-number
"""
def isHappyNumber1(num):    
    rem = sum = 0    
        
    #Calculates the sum of squares of digits    
    while(num > 0):    
        rem = num%10    
        sum = sum + (rem*rem) 
        num = num/10   #<-- num = num//10 
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
    while(num > 1):    #<--- while(num > 0):
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

