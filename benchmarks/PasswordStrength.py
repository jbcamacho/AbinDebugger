"""
Given a string representing a password, this benchmark checks the password strength.
:param s: A string.
:type  s: str
:rtype: Tuple[int, int, int, int, int, int]

{
    "benchmark_name": "PasswordStrength",
    "benchmark_metadata": [
        {
            "Function": ["check_password_strength"],
            "Bug": [ {"Position": 38, "LOC": "whitespace_count = 1"} ],
            "Fix": [ {"Position": 38, "LOC": "whitespace_count += 1"} ]
        }
    ]
}

The content of this file can be found in GitHub from author visheshdvivedi.
@misc{visheshdvivedi,
    title={Top-10-easy-python-project-ideas-for-beginners/password_strength_checker.py},
    url={https://github.com/visheshdvivedi/Top-10-Easy-Python-Project-Ideas-For-Beginners/blob/main/password_strength_checker.py},
    journal={GitHub},
    author={Visheshdvivedi}} 
"""

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
            whitespace_count = 1 # <-- FIX whitespace_count += 1
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
    
    return (strength, lower_alpha_count, upper_alpha_count, number_count, whitespace_count, special_char_count)