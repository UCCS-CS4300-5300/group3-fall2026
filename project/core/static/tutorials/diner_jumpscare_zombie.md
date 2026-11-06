# Jumpscare: The Short-Order Cook

**The Diner · Functions · Jump Scare**

> The grill hisses. The cook is still wearing the apron, and still holding the spatula, and is coming over the counter.

## What's happening

A function is supposed to cook an order and hand back the bill, but the call and the function don't agree with each other. The program crashes when it tries to use the bill.

## How to debug fast

1. **Compare the call with the definition.** Are the arguments in the same order as the parameters?
2. **Check what comes back.** If a function has no `return`, calling it gives `None`.
3. **Read the error.** `unsupported operand type(s) for *: 'NoneType' and 'float'` means you're doing math on `None`.

## Bugs to look for

- **Arguments in the wrong order.** Python matches by position: the first argument goes into the first parameter. Swap them, or use keyword arguments.
- **A missing return.** `print()` inside a function shows a value, but doesn't hand it back.

```python
def price(qty):
    total = qty * 2
    return total      # without this, price(3) is None

print(price(3))       # 6
```

## Checklist

- Does each parameter receive the value you expect?
- Does the function return the total?
- Is the bill a number before you do math on it?
