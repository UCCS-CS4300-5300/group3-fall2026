# Base Case Room

**The Funhouse · Recursion · Room 1**

> A hall of mirrors. Every reflection holds a smaller reflection, and another inside that, until you can't tell where it ends. It has to end somewhere.

## What you'll learn

- What **recursion** is: a function that calls itself
- The **base case**: the condition that stops the recursion
- The **recursive case**: the call that moves toward the base case
- Why a missing base case crashes your program

## The idea

A recursive function solves a problem by solving a **smaller version of the same problem**, then using that answer.

```python
def countdown(n):
    if n == 0:             # base case
        print("Liftoff!")
        return
    print(n)
    countdown(n - 1)       # recursive case: a smaller problem

countdown(3)
```

Output:

```
3
2
1
Liftoff!
```

## Two parts, every time

Every recursive function needs both:

1. **Base case**: the simplest version, answered directly with **no** recursive call. This is what stops it.
2. **Recursive case**: calls the function again on a **smaller** input, so each call gets closer to the base case.

If either part is missing or wrong, the function never stops.

## Recursion that returns a value

Here's a sum of 1 to n, done recursively:

```python
def total(n):
    if n == 0:
        return 0
    return n + total(n - 1)

print(total(4))    # 4 + 3 + 2 + 1 + 0 = 10
```

Read it as: "the total of 4 is 4 plus the total of 3", and so on, until "the total of 0 is 0".

## Choosing the base case

Ask: **what's the smallest input I can answer without thinking?** Sometimes there's more than one, or the input can skip past it.

```python
def every_other(n):
    if n <= 0:            # catches both 0 and negatives
        return 0
    return n + every_other(n - 2)

print(every_other(5))     # 5 + 3 + 1 = 9
```

Because this steps by 2, an odd `n` jumps right over 0. Using `<= 0` instead of `== 0` makes sure it still stops.

## When it never stops

Without a working base case, Python keeps calling until it runs out of room and raises:

```
RecursionError: maximum recursion depth exceeded
```

That's your signal to check the base case and whether each call really gets smaller.

## Common mistakes

- **No base case at all.**
- **A base case the input can skip over**, like `== 0` when stepping by 2.
- **Not getting smaller.** `f(n)` calling `f(n)` (or `f(n + 1)`) never reaches the base.
- **Forgetting to `return`** the recursive result, so the answer is lost.
