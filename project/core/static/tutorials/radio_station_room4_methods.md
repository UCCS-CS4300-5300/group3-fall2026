# Methods Room

**The Radio Station · Strings · Room 4**

> The transmission log is a mess of repeated words and garbled phrases. Strings come with tools to clean that up.

## What you'll learn

- What a method is: a function attached to a value, called with a dot
- Changing case: `.upper()`, `.lower()`, `.capitalize()`
- Searching: `.count()`, `.find()`, `in`
- Cleaning: `.strip()`, `.replace()`
- Splitting and joining: `.split()`, `.join()`

## Methods

A **method** is called on a value with a dot: `value.method()`. String methods **return a new string**; they never change the original.

```python
msg = "help"
loud = msg.upper()
print(msg, loud)    # help HELP
```

## Changing case

```python
s = "sOs NOW"
print(s.upper())        # SOS NOW
print(s.lower())        # sos now
print(s.capitalize())   # Sos now  (first letter up, rest down)
```

## Searching

```python
log = "water... static... water"
print(log.count("water"))   # 2
print(log.find("static"))   # 9   (index of first match)
print(log.find("food"))     # -1  (not found)
print("static" in log)      # True
```

## Cleaning

```python
raw = "   over and out   "
print(raw.strip())              # "over and out"
print("A-B-C".replace("-", " "))  # "A B C"
```

## Splitting and joining

`.split()` breaks a string into a **list** of words (on spaces by default, or on any separator you give it). `.join()` does the reverse: it glues a list together with the string you call it on.

```python
words = "north east south".split()
print(words)                # ['north', 'east', 'south']
print(" | ".join(words))    # north | east | south
print("x,y,z".split(","))   # ['x', 'y', 'z']
```

Combine this with list tools to rearrange words. For example, `words[::-1]` reverses the list.

## Chaining

Because methods return new strings, you can chain them:

```python
print("  mayday ".strip().upper())   # MAYDAY
```

## Common mistakes

- **Expecting a method to change the original.** `s.upper()` on its own does nothing to `s`; save the result.
- **Forgetting the parentheses.** `s.upper` is the method itself, not its result.
- **Calling `.join()` on the list.** It's `" ".join(words)`, not `words.join(" ")`.
- **Assuming `.find()` crashes.** It returns `-1` when nothing is found.
