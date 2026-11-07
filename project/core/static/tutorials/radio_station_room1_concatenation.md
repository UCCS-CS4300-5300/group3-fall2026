# Concatenation Room

**The Radio Station · Strings · Room 1**

> The transmitter still works. All you have to do is put the right words together and send them.

## What you'll learn

- Joining strings with `+`
- Repeating strings with `*`
- Turning numbers into text with `str()`
- Building messages with **f-strings**

## Joining with +

`+` sticks strings together end to end. It doesn't add spaces for you.

```python
first = "Night"
second = "Owl"
print(first + second)        # NightOwl
print(first + " " + second)  # Night Owl
```

## Repeating with *

`*` repeats a string a number of times. It's handy for borders and dividers:

```python
print("=" * 12)       # ============
print("ha" * 3)       # hahaha
```

You can use `len()` to make a line exactly as long as some text:

```python
title = "MAYDAY"
print(title)
print("-" * len(title))
```

## Numbers need str()

`+` won't join a string and a number:

```python
channel = 7
print("Channel " + channel)       # TypeError!
print("Channel " + str(channel))  # Channel 7
```

## f-strings: the easy way

Put an `f` before the opening quote, and write variables inside `{ }`. Python fills them in and converts numbers for you.

```python
name = "Jules"
freq = 98.3
print(f"{name} is broadcasting on {freq} FM")
# Jules is broadcasting on 98.3 FM
```

You can put expressions inside the braces too:

```python
print(f"Signal strength: {freq * 2}")
print(f"Loud: {name.upper()}")
```

## Wrapping text

Building a string around another one is just joining pieces in the right order:

```python
word = "help"
print("[" + word + "]")     # [help]
print(f"<<{word}>>")        # <<help>>
```

## Common mistakes

- **Forgetting spaces.** `"Hello" + "there"` gives `Hellothere`.
- **Joining a number with `+`** without `str()`.
- **Forgetting the `f`** in an f-string, which prints the braces literally.
- **Mismatched quotes**, like `"text'`.
