# Jumpscare: The Clown

**The Funhouse · Recursion · Jump Scare**

> The music box winds down. The lid creeps open. The countdown on the wall should have reached zero by now, but it just keeps going.

## What's happening

A recursive countdown should count down to zero, shout, and stop. Instead it runs until Python gives up with a `RecursionError`.

## How to debug fast

1. **Find the base case.** What condition is supposed to stop the recursion?
2. **Trace the values.** Write down `n` for each call. Does it ever land exactly on the base case?
3. **Check what happens at the base case.** Does the function actually stop there, or does it carry on to the recursive call anyway?

## Bugs to look for

- **Steps that skip the base case.** If `n` goes down by the wrong amount, it can jump straight past the value the base case checks for.
- **A base case that doesn't return.** Printing a message isn't enough. Without `return` (or an `else`), the code after the base case still runs, and the recursion continues.

```python
def down(n):
    if n == 0:
        print("Done")
        return          # stop here!
    print(n)
    down(n - 1)
```

## Checklist

- Does `n` hit the base case value exactly?
- Does the function stop at the base case?
- Does the output end exactly where it should?
