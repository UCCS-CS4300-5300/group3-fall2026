# For Room

**The Laundromat · Loops · Room 1**

> Rows and rows of washing machines. Checking each one by hand would take all night, and the night isn't safe.

## What you'll learn

- Repeating code with a `for` loop
- Counting with `range()`
- Using the loop variable inside the loop
- Combining a loop with `if`
- Printing on one line with `end=`

## The idea

A `for` loop runs the same block once for **each item** in a sequence. The **loop variable** holds the current item.

```python
for machine in range(1, 6):
    print("Checking machine", machine)
```

Output:

```
Checking machine 1
Checking machine 2
Checking machine 3
Checking machine 4
Checking machine 5
```

## range()

`range()` produces a sequence of whole numbers. The **stop value is never included**.

```python
range(5)          # 0, 1, 2, 3, 4
range(1, 6)       # 1, 2, 3, 4, 5
range(0, 20, 5)   # 0, 5, 10, 15      (third number is the step)
range(10, 0, -2)  # 10, 8, 6, 4, 2   (counting down)
```

To include a number, stop **one past** it: `range(1, 11)` goes up to 10.

## Loops and if together

Put an `if` inside the loop to act only on some items.

```python
for n in range(1, 21):
    if n % 4 == 0:
        print(n, "is a multiple of 4")
```

`and` lets you require two things at once: `if n % 2 == 0 and n % 3 == 0:`.

## Printing on one line

By default `print()` ends with a new line. Change that with `end=`:

```python
for n in range(1, 6):
    print(n, end=" ")
print()          # finish the line
# 1 2 3 4 5
```

## Loops over other things

`for` works on anything you can step through, not just numbers:

```python
for letter in "RUN":
    print(letter)

for item in ["rope", "torch", "map"]:
    print("Packed:", item)
```

## Common mistakes

- **Off-by-one with `range`.** `range(1, 10)` stops at 9.
- **Forgetting the colon** after the `for` line.
- **Not indenting the body**, or indenting code that should run *after* the loop.
- **Checking conditions in the wrong order.** If a number can match two tests, check the "both" case first.
