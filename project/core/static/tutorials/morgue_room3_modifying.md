# Modifying Room

**The Morgue · Arrays · Room 3**

> Drawers get emptied, records get added, mistakes get corrected. A list is only useful if you can change it.

## What you'll learn

- Changing an item by index
- Adding items with `.append()` and `.insert()`
- Removing items with `.pop()` and `.remove()`
- Why you remove from the **end first** when removing several indexes
- Building a new list without duplicates

## Changing an item

Assign to an index to replace what's there:

```python
shelf = ["rope", "torch", "map"]
shelf[1] = "flashlight"
print(shelf)    # ['rope', 'flashlight', 'map']
```

## Adding items

```python
shelf.append("radio")          # add to the end
shelf.insert(0, "knife")       # add at index 0, shifting the rest right
print(shelf)   # ['knife', 'rope', 'flashlight', 'map', 'radio']
```

## Removing items

```python
last = shelf.pop()       # removes and returns the last item
first = shelf.pop(0)     # removes and returns the item at index 0
shelf.remove("map")      # removes the first matching value
```

`.pop()` gives you back what it removed, so you can print or use it. `.remove()` doesn't.

## Removing several indexes: go from the end

Removing an item **shifts everything after it one place left**. If you remove index 0 first, every later index is now off by one.

```python
items = ["a", "b", "c", "d", "e"]
# remove indexes 1 and 3
for i in [3, 1]:          # largest first!
    print("Removed", items.pop(i))
print(items)              # ['a', 'c', 'e']
```

Removing from the highest index down means the earlier positions haven't moved yet. `sorted(indexes, reverse=True)` puts any list of indexes in that order.

## Building a new list

Often it's easier and safer to build a **new** list than to change the one you're looping over:

```python
readings = [5, 3, 5, 8, 3]
unique = []
for r in readings:
    if r not in unique:
        unique.append(r)
print(unique)    # [5, 3, 8]  (original order kept)
```

## Common mistakes

- **Removing from the front first** when deleting several indexes.
- **Changing a list while looping over it**, which skips items. Build a new list instead.
- **Calling `.remove()` with an index.** `.remove()` takes a *value*; `.pop()` takes an *index*.
- **Expecting `.append()` to return the list.** It returns `None`; it changes the list in place.
