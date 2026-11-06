# Else-If Room

**The Police Station · Conditionals · Room 2**

> The threat board has more than two settings. "Safe" and "danger" aren't enough anymore.

## What you'll learn

- Checking several conditions in a row with `elif`
- How Python picks **the first** true branch and skips the rest
- Why the order of your conditions matters

## The idea

`elif` means "else, if". It lets you test another condition when the earlier ones were False.

```python
zombies = 7

if zombies == 0:
    print("Safe")
elif zombies < 5:
    print("Be careful")
elif zombies < 10:
    print("Hide")
else:
    print("Run!")
```

Python checks from top to bottom. As soon as one condition is True, it runs that block and **skips all the rest**. `else` (optional) runs only if nothing above matched.

## Order matters

Because only the first match runs, a broad condition placed early can "steal" cases meant for a more specific one later.

```python
score = 95

# Wrong order: 95 > 50 is True, so we never reach the > 90 check
if score > 50:
    print("Pass")
elif score > 90:
    print("Excellent")
```

Fix it by putting the **most specific** (or highest) condition first:

```python
if score > 90:
    print("Excellent")
elif score > 50:
    print("Pass")
```

## Several things equal?

You can chain comparisons and combine them:

```python
a, b, c = 4, 4, 9
if a == b == c:
    print("All the same")
elif a == b or b == c or a == c:
    print("Two match")
else:
    print("All different")
```

## Handling bad input first

It's a good habit to reject invalid values at the top of the chain:

```python
age = -2
if age < 0:
    print("Invalid age")
elif age < 13:
    print("Child")
else:
    print("Teen or adult")
```

## Common mistakes

- **Writing `else if`** (two words). Python uses `elif`.
- **Using several `if`s instead of `elif`.** Separate `if`s are all checked, so more than one can run.
- **Wrong order**, so a later branch can never run.
- **Forgetting the colon** after each `elif ...:`.
