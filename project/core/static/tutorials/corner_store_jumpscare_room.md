# Jumpscare: The Cashier

**The Corner Store · Variables & Data Types · Jump Scare**

> The cashier was never gone. The register prints an error, and something behind the counter starts to move. Fix the code before it reaches you.

## What's happening

A jumpscare gives you **broken code** and very little time. Your job is to **debug**: find what's wrong, fix it, and run it again. This one is all about **data types**.

## How to debug fast

1. **Read the error message.** The last line tells you the error type and usually the line number.
2. **Check every value's type.** Ask: is this a number or text? Quotes make it text.
3. **Fix one thing at a time**, then run again. There may be more than one bug.

## Errors you'll likely see

**TypeError: can't multiply sequence by non-int of type 'float'**
You tried to multiply a *string* by a decimal number. Text and numbers don't mix in math. Make sure numbers are stored as numbers, or convert with `int()` / `float()`.

**TypeError: can only concatenate str (not "float") to str**
You used `+` to join text and a number. Either convert the number with `str()`, or pass both to `print()` separated by a comma.

```python
total = 9.0
print("Total:", total)          # works
print("Total: " + str(total))   # also works
```

## Checklist

- Are any numbers wrapped in quotes by accident?
- Is every `+` joining two things of the **same** type?
- Does the output match what the register is supposed to print?
