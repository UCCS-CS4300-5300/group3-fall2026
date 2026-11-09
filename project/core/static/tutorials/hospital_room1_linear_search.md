# Linear Search Room

**The Hospital · Searching & Sorting · Room 1**

> The patient list is a mess, in no particular order. The only way to find someone is to check every bed, one at a time.

## What you'll learn

- **Linear search**: checking items one by one until you find a match
- Returning a **position**, or a "not found" value
- Stopping early once you've found what you need
- Finding the smallest or largest item yourself
- Why linear search can take up to **n** checks

## The idea

Start at the beginning. Look at each item. If it's the one you want, stop. If you reach the end without finding it, it isn't there.

```python
def find(items, target):
    for i in range(len(items)):
        if items[i] == target:
            return i          # found: stop now
    return -1                 # checked everything: not found

wards = [14, 3, 27, 9, 31]
print(find(wards, 9))    # 3
print(find(wards, 50))   # -1
```

`-1` is a common "not found" signal, because it can never be a real index from the front.

## Returning more than one value

A function can return a **tuple** of values, then you can unpack them:

```python
def find(items, target):
    for i, x in enumerate(items):
        if x == target:
            return True, i
    return False, -1

found, where = find(wards, 27)
print(found, where)     # True 2
```

## Stop early

The `return` inside the loop ends the search as soon as there's a match. There's no point checking the rest.

The `return -1` must be **after** the loop, not inside an `else`. Otherwise you'd give up after checking only the first item.

## Finding the minimum yourself

Searching for the "best" item is also a linear scan: keep track of the best so far.

```python
temps = [("Ari", 99.1), ("Bea", 101.4), ("Cal", 98.6)]
coolest = temps[0]
for patient in temps:
    if patient[1] < coolest[1]:
        coolest = patient
print(coolest)    # ('Cal', 98.6)
```

## How fast is it?

In the worst case (the item is last or missing), linear search checks **every** item. For a list of `n` items, that's up to `n` checks. That's fine for small lists, but slow for huge ones. If the list is **sorted**, there's a faster way, coming in the next room.

## Common mistakes

- **Returning "not found" inside the loop**, which stops after the first item.
- **Returning the value instead of its position** (or the other way round).
- **Forgetting the not-found case**, so the function returns `None`.
- **Starting the minimum at 0** instead of at the first item.
