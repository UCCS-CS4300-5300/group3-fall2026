# Jumpscare: The Assembly-Line Turret

**The Factory · Classes & Objects · Jump Scare**

> The line jerks back to life. A turret on the ceiling swivels toward you, and something with too many arms climbs down the conveyor.

## What's happening

A `Turret` class should start with some ammo and lose one round each time it fires. The class has setup mistakes, a method uses the wrong variable, and one shot is never actually fired.

## How to debug fast

1. **Read the error.** `TypeError: __init__() takes 1 positional argument but 2 were given` usually means `self` is missing from a method's parameters. `UnboundLocalError` or `NameError` inside a method usually means a missing `self.`.
2. **Check every method's first parameter.** It should be `self`.
3. **Check every attribute use inside the class.** It should start with `self.`.
4. **Check every call.** Does it have parentheses?

## Bugs to look for

- **Missing `self`** as the first parameter of a method.
- **Using a bare name instead of `self.name`**, so the method works on a local variable that doesn't exist.
- **A method referenced but not called.** Without `()`, nothing happens and no error appears.

```python
class Lamp:
    def __init__(self, on):
        self.on = on

    def toggle(self):
        self.on = not self.on

lamp = Lamp(False)
lamp.toggle()       # needs the parentheses
print(lamp.on)      # True
```

## Checklist

- Does every method start with `self`?
- Does every attribute inside the class use `self.`?
- Does every method call end in `()`?
- Does the ammo count go down by one per shot?
