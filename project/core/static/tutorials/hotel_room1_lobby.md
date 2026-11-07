# Key-Value Room

**The Hotel · Dictionaries / Maps · Room 1 (Lobby)**

> Behind the front desk: a wall of pigeonholes, each with a room number and a name. You don't search every box. You go straight to the right one.

## What you'll learn

- What a dictionary is: a collection of **key → value** pairs
- Creating a dictionary with `{ }`
- Looking up a value by its key
- Checking whether a key exists with `in`
- Safe lookups with `.get()` and a default
- Getting all values with `.values()`

## The idea

A list finds things by **position** (0, 1, 2…). A **dictionary** finds things by a **key** you choose, like a room number or a name.

```python
guests = {
    204: "Ivy Park",
    305: "Omar Diaz",
    410: "Lena Fox",
}
```

Each entry is `key: value`, separated by commas, inside curly braces. Keys must be unique.

## Looking up a value

Put the key in square brackets:

```python
print(guests[305])     # Omar Diaz
```

If the key doesn't exist, you get a `KeyError`:

```python
print(guests[999])     # KeyError: 999
```

## Is the key there?

`in` checks the **keys** of a dictionary:

```python
if 410 in guests:
    print("Room 410:", guests[410])
else:
    print("Room 410 is empty")
```

## .get(): lookup without crashing

`.get(key)` returns the value, or `None` if the key is missing. Give it a second argument to use as a default:

```python
print(guests.get(204))               # Ivy Park
print(guests.get(999))               # None
print(guests.get(999, "Vacant"))     # Vacant
```

## Keys, values and the biggest one

```python
rates = {"single": 80, "double": 120, "suite": 300}
print(list(rates.keys()))     # ['single', 'double', 'suite']
print(list(rates.values()))   # [80, 120, 300]
print(sum(rates.values()))    # 500
```

To find the **key** with the largest value, `max()` can compare using the dictionary's lookup:

```python
print(max(rates, key=rates.get))   # suite
```

## Common mistakes

- **Looking up a missing key with `[ ]`**, which crashes. Use `in` or `.get()`.
- **Expecting `in` to search values.** It checks keys. Use `x in d.values()` for values.
- **Mixing key types.** `204` (a number) and `"204"` (text) are different keys.
- **Forgetting the colon** between key and value.
