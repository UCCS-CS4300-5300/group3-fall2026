# Jumpscare: The Patrol Officer

**The Police Station · Conditionals · Jump Scare**

> Boots on tile. The officer behind you still has a badge, but no pulse. The threat display is showing the wrong warning.

## What's happening

The threat display uses an `if` / `elif` / `else` chain, and it's broken in more than one way. Some bugs stop the code running at all; one makes it run but print the wrong thing.

## How to debug fast

1. **Fix syntax errors first.** Python won't run anything until they're gone. The error message points to the line.
2. **Then trace the logic.** Pick the actual value and walk through the chain top to bottom. Which branch runs first?

## Bugs to look for

- **Assignment vs comparison.** `=` stores a value; `==` compares. Only one belongs inside an `if`.
- **Missing colons.** Every `if`, `elif` and `else` line ends with `:`.
- **Unreachable branches.** If an earlier condition is broader, a later, more specific one never gets a chance. Put the most specific check first.

```python
# Which line prints when n = 20?
if n > 5:
    print("A")
elif n > 15:
    print("B")   # never runs for n > 5!
```

## Checklist

- Does the code run without a `SyntaxError`?
- With the given number of zombies, does the right message print?
- Could any branch never be reached?
