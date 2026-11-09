# Variables Room

**The Corner Store · Variables & Data Types · Room 1**

> The register is dead, but the shelves still hold what you need. Before you can take stock, you need somewhere to *keep* things.

## What you'll learn

- What a variable is
- Creating a variable with `=`
- Rules and good habits for naming variables
- Printing a variable's value with `print()`
- Changing (reassigning) a variable

## The idea

A **variable** is a name that points to a value. Think of it as a label you stick on a box: the label is the name, and whatever is inside the box is the value.

You create a variable with an **assignment**: the name goes on the left, `=` in the middle, and the value on the right.

```python
water_bottles = 4
store_name = "Quick Mart"
```

`=` does not mean "is equal to" in Python. It means **"store the value on the right under the name on the left."** Python works out the right side first, then saves it.

## Using a variable

Once a value has a name, you can use the name anywhere you would use the value.

```python
water_bottles = 4
print(water_bottles)          # 4
print("Bottles:", water_bottles)   # Bottles: 4
```

`print()` can take several values separated by commas. It puts a space between them, so you can mix text and numbers freely.

## Changing a variable

A variable can be given a new value at any time. The old value is replaced.

```python
water_bottles = 4
water_bottles = water_bottles - 1   # drank one
print(water_bottles)                # 3
```

Python reads `water_bottles - 1` first (4 - 1 = 3), then stores 3 back under the same name.

You can also assign several variables in one line:

```python
x, y = 10, 20
print(x, y)   # 10 20
```

## Naming rules

- Names can contain letters, digits and underscores: `can_count`, `shelf2`
- A name **cannot start with a digit**: `2shelf` is an error
- No spaces or dashes: use `canned_beans`, not `canned beans` or `canned-beans`
- Names are **case-sensitive**: `Total` and `total` are different variables
- Don't use Python keywords such as `if`, `for` or `class`, and avoid built-in names such as `print`, `list` or `type`

Good names describe what they hold. `price` beats `p`, and `survivor_name` beats `x`.

## Common mistakes

- **Using a variable before creating it.** `print(score)` before `score = ...` raises `NameError`.
- **Reversing the assignment.** `4 = bottles` is an error; the name always goes on the left.
- **Forgetting quotes around text.** `name = Maya` looks for a *variable* called `Maya`. Text needs quotes: `name = "Maya"`.
- **Typos in names.** `bottels` and `bottles` are two different names to Python.
