# Logic Room

**The Police Station · Conditionals · Room 4**

> The evidence locker needs two officers' codes. Neither one alone is enough. Some doors need more than one condition.

## What you'll learn

- Combining conditions with `and`, `or` and `not`
- Grouping conditions with parentheses
- Checking membership with `in`
- Range checks like `0 <= x <= 10`

## and, or, not

- `a and b` is True only if **both** are True.
- `a or b` is True if **at least one** is True.
- `not a` flips True to False and False to True.

```python
has_key = True
door_jammed = False

print(has_key and not door_jammed)   # True
print(has_key or door_jammed)        # True
print(not has_key)                   # False
```

## Using them in an if

```python
ammo = 4
health = 70

if ammo > 0 and health > 50:
    print("Fight")
elif ammo == 0 or health < 20:
    print("Run")
else:
    print("Hide")
```

## Parentheses make intent clear

`and` is checked before `or`, which can surprise you. Parentheses remove any doubt:

```python
# Open if it's day, OR if it's night and you have a light
if is_day or (is_night and has_flashlight):
    print("Go outside")
```

## Ranges

Python lets you chain comparisons, which is perfect for "between" checks:

```python
temp = 72
if 60 <= temp <= 80:
    print("Comfortable")
```

## The in operator

`in` checks whether a value appears in a collection or a string:

```python
safe_codes = [1234, 4321, 1111]
print(4321 in safe_codes)     # True
print("a" in "radio")         # True
print("z" not in "radio")     # True
```

## Thinking about calendar ranges

When a range wraps across a boundary (like a season that runs from December into March), it's often easiest to break it into separate pieces and join them with `or`:

```python
# "late December or any of Jan–Feb or early March"
if (month == 12 and day >= 21) or month in (1, 2) or (month == 3 and day <= 19):
    print("winter")
```

## Common mistakes

- **Writing `x == 1 or 2`.** That's always True. Write `x == 1 or x == 2`, or `x in (1, 2)`.
- **Mixing `and` and `or` without parentheses** and getting a different grouping than you meant.
- **Using `&&`, `||` or `!`.** Those are from other languages. Python uses the words `and`, `or`, `not`.
- **Forgetting edge values**: is the boundary day included or not?
