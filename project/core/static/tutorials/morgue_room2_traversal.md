# Traversal Room

**The Morgue · Arrays · Room 2**

> Clipboards, scales, tags. Somebody has to go through every record, one at a time.

## What you'll learn

- Visiting every item with `for item in list`
- Looping by index with `range(len(list))`
- Running totals and running maximums
- Filtering items with `if` inside the loop
- Using `enumerate()` to get both index and item

## Visiting every item

The simplest way to go through a list:

```python
crates = [4, 9, 2, 7]
for c in crates:
    print("Crate with", c, "items")
```

`c` takes each value in turn. You don't need indexes at all.

## Looping by index

When you need the position too, loop over the indexes:

```python
for i in range(len(crates)):
    print("Crate", i, "has", crates[i])
```

`enumerate()` gives you both at once and is usually cleaner:

```python
for i, c in enumerate(crates):
    print("Crate", i, "has", c)
```

## Running total

Start a total at 0 **before** the loop, and add to it **inside**:

```python
total = 0
for c in crates:
    total += c
print("Total:", total)    # 22
```

## Running maximum

Start with the first item, then replace it whenever you see something bigger:

```python
biggest = crates[0]
for c in crates:
    if c > biggest:
        biggest = c
print("Biggest:", biggest)   # 9
```

You can track a total and a maximum in the **same** loop.

## Filtering

Use an `if` inside the loop to pick out items:

```python
names = ["ana", "bo", "kit", "lee"]
for n in names:
    if len(n) == 3:
        print(n)
# ana, kit, lee
```

Strings can be indexed too, so `word[0]` is the first letter and `word[-1]` is the last.

## Common mistakes

- **Resetting the total inside the loop**, so it only keeps the last value.
- **Writing `total = c` instead of `total += c`.**
- **`range(len(list) + 1)`**, which goes one index too far.
- **Starting the maximum at 0**, which breaks if all values are negative.
