# Scope Room

**The Diner · Functions · Room 3**

> Two cooks, one kitchen. Each writes their own special on their own notepad, but there's only one board on the wall.

## What you'll learn

- **Local** variables: created inside a function and only visible there
- **Global** variables: created outside any function
- How a local name **hides** a global one with the same name
- Changing a global from inside a function with `global`

## Local variables

A variable created inside a function exists **only while that function runs**. Outside, it doesn't exist.

```python
def make_soup():
    pot = "tomato"
    print(pot)

make_soup()     # tomato
print(pot)      # NameError: name 'pot' is not defined
```

## Global variables

A variable created at the top level of your program is **global**. Functions can **read** it:

```python
diner = "Rusty Spoon"

def sign():
    print("Welcome to", diner)

sign()          # Welcome to Rusty Spoon
```

## Same name, different variable

If a function **assigns** to a name, Python treats that name as **local** to the function. It hides the global one, which stays unchanged.

```python
soup = "chicken"

def night_shift():
    soup = "mystery"       # a new local variable
    print("Night:", soup)

night_shift()              # Night: mystery
print("Board:", soup)      # Board: chicken
```

## Changing a global: the global keyword

To change the global variable from inside a function, declare it with `global` first:

```python
orders = 0

def take_order():
    global orders
    orders += 1
    print("Orders so far:", orders)

take_order()    # 1
take_order()    # 2
```

Without `global orders`, the line `orders += 1` would raise `UnboundLocalError`, because Python thinks `orders` is local but it hasn't been given a value yet.

## Good habits

`global` works, but it makes code harder to follow. Often it's cleaner to **pass values in** as parameters and **return** the new value:

```python
def take_order(count):
    return count + 1

orders = take_order(orders)
```

## Common mistakes

- **Using a local variable outside its function.**
- **Expecting an assignment inside a function to change a global** without `global`.
- **`UnboundLocalError`** from `x += 1` on a global without declaring it.
- **Putting `global` after using the variable.** Declare it at the top of the function.
