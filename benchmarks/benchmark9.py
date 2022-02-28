"""

"benchmark_metadata": {[
    {
        "Function": [''],
        "Bug": [('', '')],
        "Fix": [('', '')]
    }
]}
The content of this file can be found in geeksforgeeks.
@misc{geeksforgeeks_2021,
	title={Check whether a number has consecutive 0's in the given base or not},
	url={https://www.geeksforgeeks.org/check-whether-a-number-has-consecutive-0s-in-the-given-base-or-not/},
	journal={GeeksforGeeks}, author={GeeksforGeeks}, year={2021}, month={Apr}
} 
"""
# Python implementation of the above approach

# We first convert to given base, then
# check if the converted number has two
# consecutive 0s or not
def hasConsecutiveZeroes(N, K):
	z = toK(N, K)
	if (check(z)):
		print("Yes")
	else:
		print("No")

# Function to convert N into base K
def toK(N, K):

	# Weight of each digit
	w = 1
	s = 0
	while (N != 0):
		r = N % K
		N = N//K
		s = r * w + s
		w = 10
	return s

# Function to check for consecutive 0
def check(N):

	# Flag to check if there are consecutive
	# zero or not
	fl = False
	while (N != 0):
		r = N % 10
		N = N//10

		# If there are two consecutive zero
		# then returning False
		if (fl == True and r == 0):
			return False
		if (r > 0):
			fl = False
			continue
		fl = True
	return True

# Driver code
N, K = 15, 8
hasConsecutiveZeroes(N, K)
