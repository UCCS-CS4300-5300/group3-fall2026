# Jumpscare: The Spinning Drum

**The Laundromat · Loops · Jump Scare**

> A dryer door bangs open. Something tumbles out that was definitely not laundry. The load display is stuck.

## What's happening

The load counter uses a `while` loop, and it's broken. It should count through every load and then stop. Right now it either won't run, never stops, or stops too early.

## How to debug fast

1. **Fix the syntax first.** Look at the line the error points to. What does every loop line end with?
2. **Ask: what changes each pass?** If nothing in the body changes the variable in the condition, the loop never ends.
3. **Check the last value.** Does your condition include the final number, or stop one short?

## Bugs to look for

- **Missing colon** at the end of the `while` line.
- **Infinite loop**: the counter is never updated inside the loop.
- **Off-by-one**: `<` stops before the limit; `<=` includes it.

```python
count = 1
while count <= 3:
    print(count)
    count += 1     # without this line, it prints 1 forever
```

## Checklist

- Does it run without a `SyntaxError`?
- Does it stop on its own?
- Does it print the first **and** last load?
