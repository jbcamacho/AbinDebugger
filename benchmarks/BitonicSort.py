"""
Given a list of integers and two integers, this benchmark converts the list into a bitonic sequence.
A bitonic sequence is one that monotonically increases, then decreases.

"benchmark_metadata": {[
    {
        "Function": [''],
        "Bug": [('', '')],
        "Fix": [('', '')]
    }
]}
The content of this file can be found in geeksforgeeks.
@misc{geeksforgeeks_2022,
 	title={Python program for Bitonic Sort},
	 url={https://www.geeksforgeeks.org/python-program-for-bitonic-sort/},
	 journal={GeeksforGeeks}, author={GeeksforGeeks}, year={2022}, month={Jan}
} 
"""
# Python program for Bitonic Sort. Note that this program
# works only when size of input is a power of 2.

# The parameter dir indicates the sorting direction, ASCENDING
# or DESCENDING; if (a[i] > a[j]) agrees with the direction,
# then a[i] and a[j] are interchanged.*/
def compAndSwap(a, i, j, dire):
	if (dire==1 and a[i] > a[j]) or (dire==0 and a[i] > a[j]):
		a[i],a[j] = a[j],a[i]

# It recursively sorts a bitonic sequence in ascending order,
# if dir = 1, and in descending order otherwise (means dir=0).
# The sequence to be sorted starts at index position low,
# the parameter cnt is the number of elements to be sorted.
def bitonicMerge(a, low, cnt, dire):
	if cnt > 1:
		k = cnt//2
		for i in range(low , low+k):
			compAndSwap(a, i, i+k, dire)
		bitonicMerge(a, low, k, dire)
		bitonicMerge(a, low+k, k, dire)

# This function first produces a bitonic sequence by recursively
# sorting its two halves in opposite sorting orders, and then
# calls bitonicMerge to make them in the same order
def bitonicSort(a, low, cnt,dire):
	if cnt > 1:
		k = cnt//2
		bitonicSort(a, low, k, 1)
		bitonicSort(a, low+k, k, 0)
		bitonicMerge(a, low, cnt, dire)

# Caller of bitonicSort for sorting the entire array of length N
# in ASCENDING order
def aSort(a, N, up):
  bitonicSort(a, 10, N, up)
  return a
