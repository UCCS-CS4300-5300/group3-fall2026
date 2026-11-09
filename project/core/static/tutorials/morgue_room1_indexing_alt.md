# Indexing Room

**The Morgue · Arrays · Room 1**

> A wall of steel drawers, each with a number. You need to know exactly which one to open, and which ones to leave shut.

## What you'll learn

- Creating a **list** (Python's array)
- Zero-based indexes: the first item is `[0]`
- Negative indexes: `[-1]` is the last item
- Finding the length with `len()`
- Finding an item's position with `.index()`
- Avoiding `IndexError`

## The idea

A **list** holds several values in order, inside square brackets, separated by commas.

```python
supplies = ["rope", "torch", "map", "radio"]
```

Each item has a position called an **index**. Counting starts at **0**, not 1.

```
index:     0        1       2       3
       ["rope", "torch", "map", "radio"]
index:    -4       -3      -2      -1
```

```python
print(supplies[0])    # rope   (first)
print(supplies[2])    # map    (third)
print(supplies[-1])   # radio  (last)
print(supplies[-2])   # map    (second to last)
```

## How many items?

`len()` gives the number of items. Because counting starts at 0, the **last index is `len(list) - 1`**.

```python
print(len(supplies))              # 4
print(supplies[len(supplies) - 1])  # radio
```

## Where is it?

`.index(value)` returns the position of the **first** match.

```python
print(supplies.index("map"))   # 2
```

If the value isn't in the list, `.index()` raises a `ValueError`. Check with `in` first if you're not sure:

```python
if "knife" in supplies:
    print(supplies.index("knife"))
else:
    print("No knife")
```

## Does that index exist?

Asking for an index that's too big causes an `IndexError`. Compare against `len()` first:

```python
drawer = 10
if drawer < len(supplies):
    print(supplies[drawer])
else:
    print("No drawer", drawer)
```

## Common mistakes

- **Starting at 1.** The first item is `[0]`; `[1]` is the *second*.
- **Using `len(list)` as an index.** It's always one past the end.
- **Calling `.index()` on a missing value**, which crashes. Check with `in` first.
- **Forgetting that `.index()` only finds the first match** when a value appears more than once.
