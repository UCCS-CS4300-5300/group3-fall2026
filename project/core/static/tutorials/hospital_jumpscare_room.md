# Jumpscare: The Night Nurse

**The Hospital · Searching & Sorting · Jump Scare**

> The call light over bed 26 blinks on. The nurse at the station stands up very slowly, and the bed finder on the screen is frozen.

## What's happening

A binary search should find beds in a sorted list. It crashes, it can get stuck, and even when it runs it misses a bed that's definitely there.

## How to debug fast

1. **Read the error.** `TypeError: list indices must be integers or slices, not float` means an index was calculated with `/`.
2. **Trace `low`, `mid` and `high`** on paper for each step. Does the range always shrink?
3. **Test the edges.** Search for the first item and the last item.

## Bugs to look for

- **Float division.** `/` always gives a float. Use `//` for indexes.
- **A range that doesn't shrink.** After checking `mid`, the next range must **exclude** it: `mid + 1` on one side, `mid - 1` on the other. Otherwise the loop can repeat forever.
- **Stopping too soon.** When `low` and `high` are equal, there's still one item to check. The loop condition must allow that.

```python
# low = 6, high = 6: one item left. Should we check it?
while low <= high:     # yes
```

## Checklist

- Is `mid` always a whole number?
- Does the range get smaller every step?
- Can it find the first item **and** the last item?
