# Recursive Problems Room

**The Funhouse · Recursion · Room 3**

> Boxes inside boxes inside boxes. A magician's hat that keeps producing rabbits. Some problems are recursive by nature.

## What you'll learn

- Spotting problems with a recursive **shape**
- Working through **nested** data, like lists inside lists
- Sequences defined by earlier terms
- Why naive recursion can repeat work, and how to avoid it

## Nested data

When data contains smaller copies of itself, recursion fits naturally. A list that can hold numbers **or** other lists:

```python
def count_numbers(items):
    count = 0
    for x in items:
        if isinstance(x, list):
            count += count_numbers(x)   # a smaller list: recurse
        else:
            count += 1                  # a plain number
    return count

print(count_numbers([1, [2, 3], [[4]], 5]))   # 5
```

The "base case" here is a plain number: it's counted directly. The recursion handles any depth of nesting without you knowing it in advance.

## Sequences built from earlier terms

Some sequences are defined in terms of themselves. For example, a value might be the previous value times 2:

```python
def doubling(n):
    if n == 0:
        return 1
    return 2 * doubling(n - 1)

print([doubling(i) for i in range(6)])   # [1, 2, 4, 8, 16, 32]
```

When a term depends on **two** earlier terms, the function makes **two** recursive calls.

## The cost of repeated calls

Two calls per step can explode. If `f(n)` calls `f(n - 1)` **and** `f(n - 2)`, then `f(n - 1)` calls `f(n - 2)` again, and so on. The same values get recomputed many times over.

```
f(5)
├── f(4)
│   ├── f(3)
│   │   ├── f(2) ...
│   │   └── f(1)
│   └── f(2) ...        ← repeated
└── f(3) ...            ← repeated
```

Small inputs are fine; big ones get very slow. One fix is to **remember** answers you've already computed:

```python
memo = {}
def f(n):
    if n in memo:
        return memo[n]
    if n < 2:
        return n
    memo[n] = f(n - 1) + f(n - 2)
    return memo[n]
```

## When to use recursion

- The data is nested or tree-shaped.
- The problem naturally breaks into smaller copies of itself.
- A loop would need you to manage your own stack.

For simple counting, a loop is usually clearer.

## Common mistakes

- **Forgetting the non-list case** when walking nested lists.
- **Missing a second base case** when a function looks back two steps.
- **Recomputing the same values** until the program crawls.
- **Not adding up the recursive results** (calling, but ignoring the return value).
