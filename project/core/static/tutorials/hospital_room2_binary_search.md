# Binary Search Room

**The Hospital · Searching & Sorting · Room 2**

> The chart rack is sorted by number. You don't need to check every chart. Open the middle, and you instantly know which half to ignore.

## What you'll learn

- **Binary search**: searching a **sorted** list by halving the range each step
- Tracking `low`, `mid` and `high`
- Writing it with a loop and with recursion
- Why it takes only about **log₂(n)** steps

## The idea

If the list is sorted, look at the **middle** item:

- If it's the target, you're done.
- If the target is **bigger**, it must be in the **right** half. Throw away the left.
- If the target is **smaller**, it must be in the **left** half. Throw away the right.

Repeat on the half that's left until you find it or there's nothing left.

## The loop version

```python
def binary_search(items, target):
    low = 0
    high = len(items) - 1
    while low <= high:
        mid = (low + high) // 2
        if items[mid] == target:
            return mid
        elif items[mid] < target:
            low = mid + 1        # search the right half
        else:
            high = mid - 1       # search the left half
    return -1

beds = [2, 5, 9, 14, 20, 27, 33]
print(binary_search(beds, 20))   # 4
print(binary_search(beds, 6))    # -1
```

## Every detail matters

- `//` not `/`: the middle index must be a whole number.
- `low = mid + 1` and `high = mid - 1`: `mid` has already been checked, so skip it. Using `low = mid` can get stuck forever.
- `while low <= high`: when `low == high`, there's still **one** item left to check.

## The recursive version

Binary search is naturally recursive: each step is the same search on a smaller range.

```python
def search(items, target, low, high):
    if low > high:                 # base case: nothing left
        return -1
    mid = (low + high) // 2
    if items[mid] == target:
        return mid
    if items[mid] < target:
        return search(items, target, mid + 1, high)
    return search(items, target, low, mid - 1)

print(search(beds, 27, 0, len(beds) - 1))   # 5
```

## How fast is it?

Each step halves what's left. For 1,000 items that's about 10 steps; for 1,000,000 items, about 20. Linear search could need a million.

**But** it only works on **sorted** lists. On an unsorted list, binary search gives wrong answers.

## Common mistakes

- **Searching an unsorted list.**
- **Using `/`**, which gives a float index and a `TypeError`.
- **`low = mid` or `high = mid`**, which can loop forever.
- **`while low < high`**, which misses the last remaining item.
