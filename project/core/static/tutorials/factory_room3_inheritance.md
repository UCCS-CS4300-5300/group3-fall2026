# Inheritance Room

**The Factory · Classes & Objects · Room 3**

> The newest machines were built from the old designs, with a few upgrades bolted on.

## What you'll learn

- Making a **subclass** that inherits from a **base class**
- Inheriting attributes and methods for free
- **Overriding** a method to change its behaviour
- Calling the parent's version with `super()`
- Checking types with `isinstance()`

## The idea

Inheritance lets a new class start with everything another class has, and then add or change things.

```python
class Vehicle:
    def __init__(self, name):
        self.name = name

    def describe(self):
        print(self.name, "moves")

class Truck(Vehicle):        # Truck inherits from Vehicle
    pass

t = Truck("Hauler")
t.describe()     # Hauler moves
```

`Truck` didn't define anything, but it has `__init__` and `describe()` from `Vehicle`.

## Overriding a method

Define a method with the same name in the subclass to replace it:

```python
class Truck(Vehicle):
    def describe(self):
        print(self.name, "hauls cargo")

Truck("Hauler").describe()    # Hauler hauls cargo
```

## super(): use the parent's version

`super()` lets the subclass call the parent's method, then add to it. It's most common in `__init__`:

```python
class Truck(Vehicle):
    def __init__(self, name, load):
        super().__init__(name)     # let Vehicle set up the name
        self.load = load           # then add Truck's own data

    def describe(self):
        super().describe()         # prints "... moves"
        print("Carrying", self.load, "kg")
```

## One method, many shapes

Each subclass can answer the same method in its own way. Code that uses them doesn't need to know which kind it has:

```python
class Square:
    def __init__(self, side):
        self.side = side
    def area(self):
        return self.side ** 2

for shape in [Square(2), Square(3)]:
    print(shape.area())
```

Combine this with inheritance and you can loop over a mixed list of subclasses, calling the same method on each.

## isinstance()

`isinstance()` is True for the object's own class **and** its parents:

```python
t = Truck("Hauler", 500)
print(isinstance(t, Truck))     # True
print(isinstance(t, Vehicle))   # True
print(isinstance(Vehicle("Cart"), Truck))   # False
```

## Common mistakes

- **Forgetting `super().__init__(...)`** in a subclass's constructor, so the parent's attributes are never set.
- **Passing `self` to `super().__init__`.** Write `super().__init__(name)`, not `super().__init__(self, name)`.
- **Misspelling the overriding method**, so the parent's version runs instead.
- **Putting the parent in the wrong place.** It's `class Child(Parent):`.
