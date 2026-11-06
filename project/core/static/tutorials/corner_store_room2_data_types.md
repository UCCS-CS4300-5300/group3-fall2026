# Data Types Room

**The Corner Store · Variables & Data Types · Room 2**

> Price tags, barcodes, an "OPEN" sign that still flickers. Everything in this store is a different *kind* of information.

## What you'll learn

- The four basic types: `int`, `float`, `str`, `bool`
- Checking a value's type with `type()`
- Converting between types with `int()`, `float()`, `str()` and `bool()`
- Why `"4"` and `4` are not the same thing

## The four basic types

- `int`: whole numbers, such as `0`, `27`, `-3`
- `float`: numbers with a decimal point, such as `2.5`, `3.75`, `-0.1`
- `str`: text (a *string* of characters), such as `"beans"`, `'Aisle 3'`, `"42"`
- `bool`: true or false, only `True` or `False`

```python
cans = 12            # int
price = 2.50         # float
item = "soup"        # str
in_stock = True      # bool
```

Notes:
- Strings go inside quotes. Single `'...'` or double `"..."` both work.
- `True` and `False` start with a capital letter and have **no** quotes.
- Anything inside quotes is a string, even `"42"`.

## Checking a type

`type()` tells you what kind of value you have.

```python
print(type(12))       # <class 'int'>
print(type(2.5))      # <class 'float'>
print(type("12"))     # <class 'str'>
print(type(False))    # <class 'bool'>
```

## Why types matter

The same operator does different things for different types:

```python
print(3 + 4)        # 7      (adds numbers)
print("3" + "4")    # 34     (joins text)
print("3" + 4)      # TypeError! can't join text and a number
```

Python will not guess what you meant. If types don't match, you must convert one of them.

## Converting between types

- `int()` makes a whole number: `int("6")` → `6`, `int(7.9)` → `7` (it cuts off the decimal)
- `float()` makes a decimal number: `float("3.75")` → `3.75`
- `str()` makes text: `str(27)` → `"27"`
- `bool()` makes True/False: `bool(0)` → `False`, `bool(5)` → `True`

```python
tag = "4"
quantity = int(tag)
print(quantity * 2)      # 8, not "44"
```

`int("3.75")` fails: `int()` can only read text that looks like a whole number. Use `float()` for decimals.

## Common mistakes

- **Doing math on text.** Values read from labels, files or `input()` are strings. Convert them first.
- **Joining text and numbers with `+`.** `"Total: " + 15` fails. Use `"Total: " + str(15)` or `print("Total:", 15)`.
- **Writing `true` instead of `True`.** Lowercase `true` is treated as an unknown variable name.
- **Expecting `int()` to round.** It chops off the decimal part; use `round()` to round.
