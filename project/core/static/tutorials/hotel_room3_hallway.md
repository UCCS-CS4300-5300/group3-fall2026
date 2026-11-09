# Iteration Room

**The Hotel · Dictionaries / Maps · Room 3 (Hallway)**

> A long hallway of doors. You need to check every one and write down what you find.

## What you'll learn

- Looping over a dictionary's keys
- Looping over key-value pairs with `.items()`
- Using `.keys()` and `.values()`
- Printing neat tables with f-string widths
- Building a dictionary inside a loop (counting)

## Looping over keys

A plain `for` loop over a dictionary gives you the **keys**:

```python
floors = {"1st": 12, "2nd": 8, "3rd": 15}
for floor in floors:
    print(floor, floors[floor])
```

## .items(): key and value together

`.items()` gives both at once, and is usually clearer:

```python
for floor, rooms in floors.items():
    print(floor, "has", rooms, "rooms")
```

## Keys and values separately

```python
print(list(floors.keys()))     # ['1st', '2nd', '3rd']
print(sum(floors.values()))    # 35
```

## Neat tables

In an f-string, `{x:<10}` pads `x` to 10 characters, left-aligned; `{x:>5}` right-aligns it in 5.

```python
print(f"{'Floor':<6}{'Rooms':>6}")
for floor, rooms in floors.items():
    print(f"{floor:<6}{rooms:>6}")
```

```
Floor  Rooms
1st       12
2nd        8
3rd       15
```

## Building a dictionary in a loop

Counting things is the classic pattern: start with an empty dictionary and add 1 for each item.

```python
colors = ["red", "blue", "red", "green", "red"]
counts = {}
for c in colors:
    counts[c] = counts.get(c, 0) + 1
print(counts)    # {'red': 3, 'blue': 1, 'green': 1}
```

To skip some items (like spaces in a sentence), add an `if` and `continue`.

Then, to find the most common:

```python
print(max(counts, key=counts.get))   # red
```

## Common mistakes

- **Expecting values when looping directly.** `for x in d` gives keys.
- **Forgetting `.items()`** and writing `for k, v in d:`, which fails.
- **Adding or removing keys while looping over the same dictionary**, which raises an error. Loop over a copy: `for k in list(d):`.
- **Counting with `counts[c] += 1`** before the key exists.
