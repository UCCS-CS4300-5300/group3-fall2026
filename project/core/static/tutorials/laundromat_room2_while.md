# While Room

**The Laundromat · Loops · Room 2**

> The dryers tick down on their own clocks. You don't know how many cycles are left. You just know when to stop.

## What you'll learn

- Repeating code with a `while` loop
- Updating the loop variable so the loop can end
- Choosing between `for` and `while`
- Pulling digits off a number with `%` and `//`

## The idea

A `while` loop keeps running **as long as its condition is True**. It checks the condition before every pass.

```python
fuel = 3
while fuel > 0:
    print("Generator running, fuel:", fuel)
    fuel -= 1
print("Out of fuel")
```

Output:

```
Generator running, fuel: 3
Generator running, fuel: 2
Generator running, fuel: 1
Out of fuel
```

## Something must change

If nothing inside the loop ever makes the condition False, the loop runs **forever**. Every `while` loop needs a line that moves it toward stopping, like `fuel -= 1` above.

## for or while?

- Use `for` when you know **how many times** (or have a list to walk through).
- Use `while` when you loop **until something happens** and you don't know when that will be.

## Building a sequence

`while` is handy when each value depends on the previous ones:

```python
a, b = 1, 1
while a < 30:
    print(a, end=" ")
    a, b = b, a + b
print()
```

This prints a sequence where each number is the sum of the two before it.

## Taking a number apart

`% 10` gives the **last digit** of a number; `// 10` **removes** it. Repeat until nothing is left:

```python
n = 503
while n > 0:
    digit = n % 10
    print(digit)
    n = n // 10
# prints 3, 0, 5
```

## Common mistakes

- **Infinite loops**: forgetting to update the variable in the condition.
- **Off-by-one**: `< 5` vs `<= 5` decides whether 5 itself is included.
- **Updating the variable outside the loop body** because of wrong indentation.
- **Missing colon** after the `while` line.
