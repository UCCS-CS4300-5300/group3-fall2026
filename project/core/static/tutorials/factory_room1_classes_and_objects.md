# Classes & Objects Room

**The Factory · Classes & Objects · Room 1**

> Blueprints are pinned to every wall. One drawing, and the line turned out a thousand machines from it.

## What you'll learn

- What a **class** is: a blueprint for making things
- What an **object** is: one thing made from that blueprint
- Defining a class with `class`
- Creating objects from a class
- Reading and changing attributes with a dot
- Telling objects apart, and the difference between `==` and `is`

## The idea

A **class** describes a kind of thing. An **object** (also called an **instance**) is one actual thing of that kind. One blueprint, many machines.

```python
class Crate:
    contents = "empty"
    weight = 0
```

`contents` and `weight` are **attributes**: data that belongs to the thing. Class names usually start with a capital letter.

## Making objects

Call the class like a function to make a new object:

```python
c1 = Crate()
c2 = Crate()
```

`c1` and `c2` are two separate crates built from the same blueprint.

## Reading and changing attributes

Use a dot: `object.attribute`.

```python
print(c1.contents)      # empty

c1.contents = "bolts"
c1.weight = 12
print(c1.contents, c1.weight)   # bolts 12
print(c2.contents)              # empty (c2 is unaffected)
```

You can even give an object a brand-new attribute:

```python
class Robot:
    pass                 # an empty class

r = Robot()
r.name = "Unit 7"
r.speed = 4
print(r.name, r.speed)
```

`pass` means "nothing here yet". It's how you write an empty block.

## Many objects in a list

Objects can go in lists like any other value:

```python
bots = [Robot(), Robot()]
bots[0].name = "A"
bots[1].name = "B"
for b in bots:
    print(b.name)
```

## Same object, or just alike?

- `is` checks whether two names point to the **same object**.
- `isinstance(obj, Class)` checks whether an object was made from a class.

```python
a = Robot()
b = Robot()
c = a
print(a is b)                 # False: two different robots
print(a is c)                 # True: the same robot, two names
print(isinstance(a, Robot))   # True
print(type(a).__name__)       # Robot
```

## Common mistakes

- **Forgetting the parentheses** when making an object: `Robot` is the class, `Robot()` is a new robot.
- **Changing the class when you meant one object.** `Crate.weight = 5` changes the blueprint; `c1.weight = 5` changes one crate.
- **Expecting two separately made objects to be the same.** They're separate, even if they look alike.
- **An empty class body.** Use `pass`.
