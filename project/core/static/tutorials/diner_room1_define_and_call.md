# Define & Call Room

**The Diner · Functions · Room 1**

> The kitchen still has a menu board and a bell. Every order follows the same steps. Why write them out every time?

## What you'll learn

- What a function is
- Defining a function with `def`
- Calling a function with `()`
- Giving a function a value to work with (a **parameter**)
- Defining once, calling many times

## The idea

A **function** is a named block of code you can run whenever you want. You **define** it once with `def`, then **call** it by name with parentheses.

```python
def ring_bell():
    print("Ding!")
    print("Order up!")

ring_bell()
ring_bell()
```

Output:

```
Ding!
Order up!
Ding!
Order up!
```

## The parts of a definition

```python
def ring_bell():
    print("Ding!")
```

- `def` starts the definition.
- `ring_bell` is the function's name (same naming rules as variables).
- `()` holds the parameters (none here).
- `:` ends the line.
- The indented block is the **body**: the code that runs when you call it.

Defining a function **doesn't run it**. Nothing happens until you call it.

## Passing a value in

Put a **parameter** name inside the parentheses. When you call the function, the value you pass (the **argument**) is stored in that parameter.

```python
def greet(name):
    print("Welcome to the diner,", name)

greet("Rosa")
greet("Theo")
```

A parameter can be anything, including a list:

```python
def list_specials(specials):
    for s in specials:
        print("-", s)

list_specials(["chili", "pie"])
```

## Why use functions?

- **No repetition**: write the steps once, use them anywhere.
- **Names explain intent**: `print_receipt()` says what the code does.
- **Easy to fix**: change the function, and every call gets the fix.

## Common mistakes

- **Forgetting to call it.** Defining isn't running.
- **Calling without parentheses.** `ring_bell` refers to the function; `ring_bell()` runs it.
- **Calling before defining.** Python reads top to bottom; define the function first.
- **Wrong indentation**, so code that should be in the body runs outside it.
