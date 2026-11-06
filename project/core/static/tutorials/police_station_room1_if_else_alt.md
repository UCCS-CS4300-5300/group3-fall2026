# If/Else Room

**The Police Station · Conditionals · Room 1**

> The front desk still has a working scanner. It just needs someone to tell it what to do *depending on* what it sees.

## What you'll learn

- Making decisions with `if` and `else`
- Comparison operators: `==`, `!=`, `<`, `>`, `<=`, `>=`
- Indented blocks and the colon `:`

## The idea

An `if` statement runs a block of code **only when a condition is True**. An `else` block runs when it's **False**. Exactly one of the two runs.

```python
zombies = 3

if zombies > 0:
    print("Lock the door!")
else:
    print("Coast is clear.")
```

## Comparison operators

Each comparison gives back `True` or `False`:

```python
print(5 == 5)    # True   equal to
print(5 != 3)    # True   not equal to
print(2 < 7)     # True   less than
print(2 > 7)     # False  greater than
print(4 <= 4)    # True   less than or equal
print(9 >= 10)   # False  greater than or equal
```

**`=` vs `==`:** a single `=` *stores* a value. A double `==` *compares* two values. Inside an `if`, you almost always want `==`.

## Indentation and colons

- The `if` line and the `else` line end with a **colon** `:`.
- The code that belongs to them is **indented** (4 spaces is standard).
- When the indentation ends, you're back outside the `if`.

```python
ammo = 0
if ammo == 0:
    print("Out of ammo!")
    print("Find a weapon.")
print("This line always runs.")
```

## Even or odd?

The modulo operator `%` from the Operators Room is perfect for this. A number is even when dividing by 2 leaves no remainder.

```python
door = 12
if door % 2 == 0:
    print("Even door")
else:
    print("Odd door")
```

## Common mistakes

- **Using `=` instead of `==`** in a condition: `if x = 5:` is a `SyntaxError`.
- **Forgetting the colon** at the end of `if ...:` or `else:`.
- **Wrong indentation**: the body must be indented, and consistently.
- **Giving `else` a condition.** `else` never has one; it catches everything that's left.
