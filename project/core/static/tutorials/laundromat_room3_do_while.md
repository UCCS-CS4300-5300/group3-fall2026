# Do-While Room

**The Laundromat · Loops · Room 3**

> The washer lock is jammed. You have to try at least one code before you know whether it works.

## What you'll learn

- The "do-while" idea: run the body **at least once**, then decide whether to repeat
- Python's version: `while True:` with `break`
- Skipping a pass with `continue`
- Reading items one at a time with `iter()` and `next()`

## The idea

A normal `while` loop checks first, so its body might never run. A **do-while** loop runs the body first, then checks. Some languages have a `do { } while` statement; Python doesn't. Instead, write an endless loop and `break` out when you're done:

```python
attempts = 0
while True:
    attempts += 1
    print("Attempt", attempts)
    if attempts == 3:
        break
print("Stopped after", attempts, "attempts")
```

The body always runs at least once, because `while True` never fails its check. `break` is the only way out.

## break and continue

- `break` leaves the loop immediately.
- `continue` skips the rest of this pass and jumps back to the top.

```python
n = 0
while True:
    n += 1
    if n == 2:
        continue      # skip printing 2
    if n > 4:
        break
    print(n)
# 1, 3, 4
```

## Reading one item at a time

`iter()` turns a list into a stream you can pull from, and `next()` takes the next item. That lets you read values inside a `while True` loop:

```python
supplies = iter(["water", "rope", "STOP", "map"])
while True:
    item = next(supplies)
    if item == "STOP":
        break
    print("Packed", item)
# Packed water, Packed rope
```

## Counting, totals and averages

Loops often keep a **counter** and a **running total** at the same time:

```python
count = 0
total = 0
# ... inside the loop:
#     count += 1
#     total += value
average = total / count
print(round(average, 2))
```

Be careful not to divide by zero if nothing was counted.

## Common mistakes

- **Forgetting the `break`**, which gives an infinite loop.
- **Putting `break` before the work**, so the last item is never handled.
- **Counting the stop marker** as if it were real data.
- **Dividing by zero** when computing an average of nothing.
