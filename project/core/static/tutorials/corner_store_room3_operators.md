# Operators Room

**The Corner Store · Variables & Data Types · Room 3**

> The stockroom clock froze at some impossible number of seconds, and the safe wants a code. Time to do some math.

## What you'll learn

- Arithmetic operators: `+`, `-`, `*`, `/`
- Floor division `//` and modulo `%`
- Powers with `**`
- Shortcut assignment: `+=`, `-=`, `*=`
- How `+` and `*` behave on strings

## Arithmetic operators

```python
print(7 + 3)    # 10   add
print(7 - 3)    # 4    subtract
print(7 * 3)    # 21   multiply
print(7 / 2)    # 3.5  divide (always gives a float)
print(7 // 2)   # 3    floor division (whole part only)
print(7 % 2)    # 1    modulo (the remainder)
print(2 ** 3)   # 8    power
```

## Floor division and modulo work as a pair

`//` tells you **how many whole times** something fits, `%` tells you **what's left over**.

```python
minutes = 135
hours = minutes // 60     # 2
leftover = minutes % 60   # 15
print(hours, "h", leftover, "min")   # 2 h 15 min
```

This pattern is how you break a big number into units: seconds into minutes, cents into dollars, and so on. Peel off the biggest unit first, then work on the remainder.

`%` is also the standard way to test divisibility: `n % 2 == 0` means `n` is even.

## Order of operations

Python follows normal math rules: `**` first, then `*` `/` `//` `%`, then `+` `-`. Use parentheses when in doubt.

```python
print(2 + 3 * 4)     # 14
print((2 + 3) * 4)   # 20
```

## Shortcut assignment

```python
ammo = 10
ammo -= 3    # same as ammo = ammo - 3  → 7
ammo *= 2    # same as ammo = ammo * 2  → 14
```

## Operators on strings

`+` **joins** strings and `*` **repeats** them:

```python
print("Aisle" + " " + "5")   # Aisle 5
print("-" * 10)              # ----------
```

You can combine this with conversion to build numbers from digits:

```python
digit = 3
print(str(digit) * 2)        # "33" (text)
print(int(str(digit) * 2))   # 33   (number again)
```

## Common mistakes

- **Expecting `/` to give a whole number.** `6 / 2` is `3.0`. Use `//` if you need an `int`.
- **Mixing up `//` and `%`.** `//` = how many fit, `%` = what's left.
- **Adding a string and a number.** `"7" + 7` is a `TypeError`.
- **Forgetting parentheses.** `total = price + tax * qty` multiplies first.
