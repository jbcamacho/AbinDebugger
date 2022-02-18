def remove_html_markup(s):
    tag = False
    quote = False
    out = ""

    for c in s:
        if c == '<' and not quote:
            tag = True
        elif c == '>' and not quote:
            tag = False
        elif c == '"' or c == "'" and tag:  # <-- FIX elif (c == '"' or c == "'") and tag:
            quote = not quote
        elif not tag:
            out = out + c
    
    return out

def remove_html_markup_fixed(s):
    tag = False
    quote = False
    out = ""

    for c in s:
        if c == '<' and not quote:
            tag = True
        elif c == '>' and not quote:
            tag = False
        elif (c == '"' or c == "'") and tag:  # <-- FIX elif (c == '"' or c == "'") and tag:
            quote = not quote
        elif not tag:
            out = out + c
    
    return out

def middle(x, y, z):
    if y < z:
        if x < y:
            return y
        elif x < z:
            return y # <-- FIX return x
    else:
        if x > y:
            return y
        elif x > z:
            return x
    return z



def get_profit(sales_today, sales_yesterday):
    accom = 0
    for key, cost in sales_yesterday.items():
        accom += cost
    for cost in sales_today.values():
        accom += cost
    return accom
    

import string

def check_password_strength(password):
    lower_alpha_count = upper_alpha_count = number_count = whitespace_count = special_char_count = 0
    for char in list(password):
        if char in string.ascii_lowercase:
            lower_alpha_count += 1
        elif char in string.ascii_uppercase:
            upper_alpha_count += 1
        elif char in string.digits:
            number_count += 1
        elif char == ' ':
            whitespace_count += 1
        else:
            special_char_count += 1
    strength = 0
    remarks = ''

    if lower_alpha_count >= 1:
        strength += 1
    if upper_alpha_count >= 1:
        strength += 1
    if number_count >= 1:
        strength += 1
    if whitespace_count >= 1:
        strength += 1
    if special_char_count >= 1:
        strength += 1

    if strength == 1:
        remarks = "That's a very bad password. Change it as soon as possible."
    elif strength == 2:
        remarks = "That's not a good password. You should consider making a tougher password."
    elif strength == 3:
        remarks = "Your password is okay, but it can be improved a lot"
    elif strength == 4:
        remarks = "Your password is hard to guess. But you can make it even more secure"
    elif strength == 5:
        remarks = "Now that's one hell of a strong password !!! Hackers don't have a chance guessing that password."

    print("Your password has:-")
    print(f"{lower_alpha_count} lowercase letters")
    print(f"{upper_alpha_count} uppercase letters")
    print(f"{number_count} digits")
    print(f'{whitespace_count} whitespaces')
    print(f"{special_char_count} special characters")
    print(f"Password score: {strength}/5")
    print(f"Remarks: {remarks}")

def PrimeChecker(a) -> bool:   
    if a > 1:  # <----  if a > 1:
        for j in range(2, int(a/2) + 1):  
            if (a % j) == 0:  
                return False  
        else:  
            return True
    else:  
        return False

def isHappyNumber(num):    
    rem = sum = 0    
        
    #Calculates the sum of squares of digits    
    while(num > 0):    #<--- while(num > 0):
        rem = num%10    
        sum = sum + (rem*rem) 
        num = num//10   
    return sum 
        
def checkHappyNumber(num):
  result = num
  while(result != 1 and result != 4):    
      result = isHappyNumber(result)    
      
  #Happy number always ends with 1    
  if(result == 1):    
      return 1
  #Unhappy number ends in a cycle of repeating numbers which contain 4    
  elif(result == 4):    
      return 0