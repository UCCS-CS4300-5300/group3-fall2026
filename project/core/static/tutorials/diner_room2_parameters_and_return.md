# Parameters & Return Room

**The Diner · Functions · Room 2**

> Behind the counter: a scale, an oven thermometer and a cash register. Each one takes something in and gives you an answer back.

## What you'll learn

- Functions with several parameters
- Sending a result back with `return`
- The difference between `print` and `return`
- Default parameter values
- Keyword arguments
- Functions that call other functions

## Several parameters

Separate parameters with commas. Arguments are matched **in order**.

```python
def order(item, quantity):
    print(quantity, "x", item)

order("pancakes", 2)   # 2 x pancakes
```

## return sends a value back

`return` ends the function and hands a value back to whoever called it. You can store it, print it, or use it in another calculation.

```python
def add_tax(price):
    return price * 1.08

bill = add_tax(10)
print(round(bill, 2))      # 10.8
```

## print vs return

- `print()` shows something on the screen. The caller gets nothing back.
- `return` gives a value back. Nothing is shown unless you print it.

A function without `return` gives back `None`.

```python
def shout(x):
    print(x.upper())

result = shout("hi")   # prints HI
print(result)          # None
```

## Default values

A parameter can have a default. If the caller leaves it out, the default is used.

```python
def brew(cups, strength="medium"):
    return f"{cups} cups, {strength}"

print(brew(2))              # 2 cups, medium
print(brew(2, "strong"))    # 2 cups, strong
```

Parameters with defaults go **after** those without.

## Keyword arguments

You can name arguments when you call. Then the order doesn't matter:

```python
print(brew(strength="weak", cups=1))
```

## Functions using functions

One function can call another, so small pieces build into bigger ones:

```python
def smaller(a, b):
    if a < b:
        return a
    return b

def smallest_of_three(a, b, c):
    return smaller(smaller(a, b), c)

print(smallest_of_three(7, 2, 5))   # 2
```

## True/False results

A function can return the result of a comparison directly:

```python
def is_open(hour, opens=6, closes=22):
    return opens <= hour <= closes
```

## Common mistakes

- **Printing instead of returning**, then trying to use the result.
- **Arguments in the wrong order.** Match the definition, or use keyword arguments.
- **Code after `return`.** It never runs.
- **Forgetting to save the returned value.** `add_tax(10)` on its own throws the answer away.
