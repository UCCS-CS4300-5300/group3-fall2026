# Updating Room

**The Hotel · Dictionaries / Maps · Room 2 (Stairwell)**

> Guests check in, guests check out, and the ledger has to keep up. Nothing in this hotel stays the same for long.

## What you'll learn

- Adding a new key
- Changing an existing value
- Updating a number with `+=`
- Removing a key with `.pop()` or `del`
- Merging two dictionaries

## Adding and changing

The same syntax does both. If the key exists, the value is **replaced**; if not, it's **added**.

```python
keys_left = {"lobby": 3, "roof": 1}
keys_left["basement"] = 2     # new key
keys_left["roof"] = 4         # changed value
print(keys_left)   # {'lobby': 3, 'roof': 4, 'basement': 2}
```

## Updating a number

```python
keys_left["lobby"] += 1       # 3 → 4
```

This only works if the key already exists. For a key that might be missing, use `.get()` with a default:

```python
keys_left["garage"] = keys_left.get("garage", 0) + 1
```

## Removing a key

```python
taken = keys_left.pop("roof")   # removes it and returns 4
del keys_left["basement"]       # removes it, returns nothing
```

Both raise `KeyError` if the key isn't there. `.pop(key, default)` won't crash.

## Merging two dictionaries

`.update()` copies another dictionary's pairs in, **overwriting** any shared keys:

```python
a = {"towels": 10, "soap": 4}
b = {"soap": 6, "sheets": 8}
a.update(b)
print(a)    # {'towels': 10, 'soap': 6, 'sheets': 8}
```

If shared keys should be **added together** instead of overwritten, loop through and add:

```python
total = dict(a)       # a copy
for item, qty in b.items():
    total[item] = total.get(item, 0) + qty
```

## How many keys?

```python
print(len(keys_left))
```

## Common mistakes

- **`d[key] += 1` on a missing key**, which is a `KeyError`. Use `.get(key, 0) + 1`.
- **Expecting `.update()` to add numbers.** It overwrites.
- **Using `.add()` or `.append()`.** Dictionaries don't have them; just assign `d[key] = value`.
- **Key typos and capitals.** `"Soap"` and `"soap"` are different keys.
