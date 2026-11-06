# Call Stack Room

**The Funhouse · Recursion · Room 2**

> A clown car pulls up. Clowns keep climbing out, then climbing back in, in perfect reverse order.

## What you'll learn

- What the **call stack** is
- How each recursive call **waits** for the one it called
- Work done "on the way down" vs "on the way back up"
- Showing the depth of each call with indentation
- Python's recursion limit

## The idea

Every time a function is called, Python puts a new **frame** on the **call stack**. The frame holds that call's own parameters and local variables. When the call returns, its frame is removed and the caller picks up where it left off.

With recursion, the stack grows with each call, then unwinds in **reverse order**.

```python
def total(n):
    if n == 0:
        return 0
    return n + total(n - 1)
```

Calling `total(3)`:

```
total(3) waits for total(2)
  total(2) waits for total(1)
    total(1) waits for total(0)
      total(0) returns 0          ← base case
    total(1) returns 1 + 0 = 1
  total(2) returns 2 + 1 = 3
total(3) returns 3 + 3 = 6
```

## Down and back up

Code **before** the recursive call runs on the way down. Code **after** it runs on the way back up, in reverse.

```python
def echo(n):
    if n == 0:
        return
    print("down", n)
    echo(n - 1)
    print("up", n)

echo(3)
```

```
down 3
down 2
down 1
up 1
up 2
up 3
```

## Seeing the depth

Pass a `depth` parameter and use it to indent, so you can watch the stack grow and shrink:

```python
def echo(n, depth=0):
    pad = "  " * depth
    if n == 0:
        print(pad + "base")
        return
    print(pad + "enter", n)
    echo(n - 1, depth + 1)
    print(pad + "leave", n)
```

## Recursing on a list

The same idea works on lists: handle the first item, recurse on the rest.

```python
def count_items(items):
    if not items:              # empty list: base case
        return 0
    return 1 + count_items(items[1:])
```

## The recursion limit

Python caps how deep the stack can go, to protect your computer's memory:

```python
import sys
print(sys.getrecursionlimit())    # usually 1000
```

Going deeper raises `RecursionError`.

## Common mistakes

- **Expecting results to appear in calling order.** Return values are combined on the way **back up**.
- **Forgetting to pass `depth + 1`** (or any changing parameter) along.
- **Thinking all calls share variables.** Each frame has its own copy of `n`.
- **Very deep recursion** that hits the limit even with a correct base case.
