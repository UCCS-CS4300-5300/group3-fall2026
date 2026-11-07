# Constructors & Methods Room

**The Factory · Classes & Objects · Room 2**

> Every machine on the line gets set up when it's built, and every one has buttons that make it do something.

## What you'll learn

- The constructor `__init__`, which sets up each new object
- What `self` means
- **Methods**: functions that belong to a class
- Methods that change an object's data
- Methods that return values

## The constructor

`__init__` (two underscores on each side) runs automatically **every time you make a new object**. It's where you give the object its starting data.

```python
class Generator:
    def __init__(self, fuel):
        self.fuel = fuel

g = Generator(20)
print(g.fuel)    # 20
```

The arguments you pass to `Generator(20)` go to `__init__`'s parameters after `self`.

## What is self?

`self` is **the object the method is working on**. When you write `self.fuel = fuel`, you're saying "store this fuel on *this particular* generator."

- Every method's **first** parameter is `self`.
- You don't pass `self` yourself; Python fills it in.
- Inside the class, always reach the object's data through `self.`.

## Methods

A **method** is a function defined inside a class. Call it on an object with a dot and parentheses:

```python
class Generator:
    def __init__(self, fuel, capacity=50):
        self.fuel = fuel
        self.capacity = capacity

    def run(self, hours):
        self.fuel -= hours * 2       # changes this object's data

    def is_empty(self):
        return self.fuel <= 0        # returns a value

g = Generator(10)
g.run(3)
print(g.fuel)          # 4
print(g.is_empty())    # False
```

## Guarding your data

Methods can check before changing anything:

```python
    def add_fuel(self, amount):
        if self.fuel + amount > self.capacity:
            self.fuel = self.capacity
        else:
            self.fuel += amount
```

The object enforces its own rules, so outside code can't put it into an impossible state by accident.

## Methods that compute

Methods often just use the object's data to calculate something:

```python
class Box:
    def __init__(self, w, h):
        self.w = w
        self.h = h

    def area(self):
        return self.w * self.h

print(Box(3, 4).area())    # 12
```

## Common mistakes

- **Forgetting `self` as the first parameter.** You'll get a `TypeError` about the number of arguments.
- **Writing `fuel` instead of `self.fuel`** inside a method. Without `self.`, it's a local variable.
- **Calling a method without parentheses.** `g.run` is the method; `g.run(3)` runs it.
- **Misspelling `__init__`** (it needs two underscores on each side). If you do, it never runs.
