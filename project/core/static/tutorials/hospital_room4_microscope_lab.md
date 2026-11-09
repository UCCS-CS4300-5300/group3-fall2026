# Sorting Room

**The Hospital · Searching & Sorting · Room 3 (Microscope Lab)**

> Sample trays, ID bracelets, triage cards, all out of order. Before you can search fast, somebody has to sort.

## What you'll learn

- What sorting means: putting items in order by comparing them
- Swapping two items in a list
- **Bubble sort**: repeatedly swap neighbours that are out of order
- **Insertion sort**: slide each item left into its correct place
- Stopping early when the list is already sorted

## Swapping

Both sorts depend on swapping two items. Python can do it in one line:

```python
items = [5, 2]
items[0], items[1] = items[1], items[0]
print(items)    # [2, 5]
```

## Bubble sort

Walk through the list comparing each pair of **neighbours**. If they're out of order, swap them. After one full pass, the largest item has "bubbled" to the end. Repeat until a pass makes no swaps.

```python
def bubble_sort(items):
    n = len(items)
    for p in range(n - 1):
        swapped = False
        for i in range(n - 1 - p):
            if items[i] > items[i + 1]:
                items[i], items[i + 1] = items[i + 1], items[i]
                swapped = True
        print("after pass", p + 1, items)
        if not swapped:
            break          # already sorted: stop early

bubble_sort([4, 1, 3, 2])
```

```
after pass 1 [1, 3, 2, 4]
after pass 2 [1, 2, 3, 4]
after pass 3 [1, 2, 3, 4]
```

The `n - 1 - p` skips the end of the list that's already sorted.

## Insertion sort

Think of sorting cards in your hand. Take each card in turn and slide it left until the card before it is smaller.

```python
def insertion_sort(items):
    for i in range(1, len(items)):
        current = items[i]
        j = i - 1
        while j >= 0 and items[j] > current:
            items[j + 1] = items[j]     # shift bigger items right
            j -= 1
        items[j + 1] = current          # drop it into the gap
        print("placed", current, items)

insertion_sort([3, 1, 2])
```

```
placed 1 [1, 3, 2]
placed 2 [1, 2, 3]
```

## How fast are they?

Both compare items in pairs, so for `n` items they can take around `n × n` steps in the worst case. That's fine for small lists. Python's built-in `sorted()` and `.sort()` use a much faster method, but writing these yourself shows how sorting actually works.

## Common mistakes

- **Going one index too far** when comparing `items[i]` and `items[i + 1]`.
- **Forgetting to reset `swapped`** at the start of each pass.
- **Losing a value when shifting** in insertion sort. Save it in `current` first.
- **Printing outside the loop** when the task asks for each step.
