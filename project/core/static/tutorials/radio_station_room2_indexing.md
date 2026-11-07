# Indexing Room

**The Radio Station · Strings · Room 2**

> The signal comes in one character at a time, crackling through the static.

## What you'll learn

- Reading single characters with `[i]`
- Negative indexes for counting from the end
- `len()` on strings
- Looping over a string, with and without indexes
- Strings can't be changed in place

## A string is a sequence

Each character in a string has an index, just like a list. Counting starts at 0.

```
 index:  0  1  2  3  4
         R  A  D  I  O
 index: -5 -4 -3 -2 -1
```

```python
word = "RADIO"
print(word[0])     # R
print(word[3])     # I
print(word[-1])    # O
print(len(word))   # 5
```

Spaces and punctuation are characters too, and they have indexes.

## Looping over characters

Loop directly when you only need the characters:

```python
for ch in "SOS":
    print(ch)
```

Loop by index, or use `enumerate()`, when you need positions:

```python
code = "SOS"
for i in range(len(code)):
    print(i, code[i])

for i, ch in enumerate(code):
    print(i, ch)
```

## Checking characters

`in` checks whether a character is in a group of characters:

```python
for i, ch in enumerate("CALL NOW"):
    if ch in "AEIOU":
        print("Vowel", ch, "at", i)
```

Combine this with a counter to count matches.

## Strings are immutable

You can **read** `word[0]`, but you can't **assign** to it:

```python
word = "RADIO"
word[0] = "B"     # TypeError: 'str' object does not support item assignment
```

To change a string, build a new one: `word = "B" + word[1:]`.

## Common mistakes

- **Starting at 1.** The first character is `[0]`.
- **Using `len(s)` as an index.** The last index is `len(s) - 1` (or just use `-1`).
- **Forgetting about spaces** when counting positions.
- **Trying to change a character in place.**
