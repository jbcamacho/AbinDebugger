"""
public static int numZero (int [ ] arr)
{​​​​​​​​​  // Effects: If arr is null throw NullPointerException
   // else return the number of occurrences of 0 in arr
   int count = 0;
   for (int i = 1; i < arr.length; i++)
   {​​​​​​​​​
      if (arr [ i ] == 0)
      {​​​​​​​​​
         count++;
      }​​​​​​​​​
   }​​​​​​​​​
   return count;
}
"""

def int_num_zeros(arr):
    if arr == []:
        raise ValueError
    count = 0
    for i in range(1, len(arr)):
    #for i in range(len(arr) - 1):
        if arr[i] == 0:
            count += 1
    return count

def int_count_zeros(arr):
    if arr == []:
        raise ValueError
    count = 0
    for n in arr:
        if arr == 0:
            count += 1
    return count


#len(list(filter(lambda x: x == 0, arr)))
