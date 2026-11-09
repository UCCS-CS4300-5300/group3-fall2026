# Switch Room

**The Police Station · Conditionals · Room 3**

> The dispatch desk has a dial with a dozen settings. Writing a dozen `elif`s feels like the slow way out.

## What you'll learn

- `match` / `case`: Python's version of a *switch* statement (Python 3.10+)
- Matching one value against several possible values
- Combining options with `|`
- The default case `case _:`

## The idea

Many languages have a `switch` statement for "compare this one value against a list of options". In Python, that's `match`.

```python
signal = "red"

match signal:
    case "green":
        print("Go")
    case "yellow":
        print("Slow down")
    case "red":
        print("Stop")
    case _:
        print("Unknown signal")
```

Python compares `signal` against each `case` from top to bottom and runs the **first** one that matches. Only one case runs.

## The default case

`case _:` matches **anything**. It works like `else` in an `if` chain, so put it **last**. If no case matches and there's no `case _`, nothing happens.

## Several values, one case

Use `|` (read it as "or") to share one block between several values:

```python
day = "Sat"

match day:
    case "Sat" | "Sun":
        print("Weekend")
    case "Mon" | "Tue" | "Wed" | "Thu" | "Fri":
        print("Weekday")
    case _:
        print("Not a day")
```

## match vs if/elif

The two are interchangeable for simple cases. `match` is cleaner when you're comparing **one value** against **many fixed options**. Use `if`/`elif` when you need ranges or more complex conditions like `x > 10`.

```python
# Same as the signal example, written with if/elif:
if signal == "green":
    print("Go")
elif signal == "yellow":
    print("Slow down")
...
```

## Upper and lower case

`"E"` and `"e"` are different strings. If case shouldn't matter, convert first:

```python
letter = "E"
match letter.lower():
    case "a" | "e" | "i" | "o" | "u":
        print("vowel")
    case _:
        print("consonant")
```

## Common mistakes

- **Putting `case _:` first.** It matches everything, so no later case would ever run.
- **Forgetting the colons** after `match ...:` and each `case ...:`.
- **Using `or` instead of `|`** between case values.
- **Running an older Python.** `match` needs Python 3.10 or newer.
