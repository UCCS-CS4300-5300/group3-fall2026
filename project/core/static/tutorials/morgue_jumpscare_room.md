# Jumpscare: The Body Bag

**The Morgue · Arrays · Jump Scare**

> The tally board is wrong, and one of the bags on the table just twitched.

## What's happening

The code should add up the bodies in every room and print the correct total. It crashes, and even once it stops crashing, the answer is wrong.

## How to debug fast

1. **Read the error.** An `IndexError: list index out of range` means you asked for a position that doesn't exist.
2. **Check the range.** For a list of length `n`, valid indexes are `0` to `n - 1`. `range(len(items))` already stops at the right place.
3. **Check the total.** Is the loop *adding* to the total, or *replacing* it each time?

## Bugs to look for

- **Going one index too far.** Adding `+ 1` to `len()` in a `range()` overshoots the last item.
- **`=` vs `+=`.** `total = x` throws away the old total; `total += x` adds to it.

```python
nums = [2, 4, 6]
total = 0
for i in range(len(nums)):   # 0, 1, 2
    total += nums[i]
print(total)    # 12
```

## Checklist

- Does the loop visit every index exactly once and no more?
- Does the total grow each pass?
- Does the final number match what the board expects?
