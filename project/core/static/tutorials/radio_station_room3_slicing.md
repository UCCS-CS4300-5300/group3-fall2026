# Slicing Room

**The Radio Station · Strings · Room 3**

> Reels of tape everywhere. The message you need is in there, somewhere in the middle, or maybe playing backwards.

## What you'll learn

- Slices: `s[start:stop]`
- Leaving out `start` or `stop`
- Steps: `s[start:stop:step]`
- Negative slices
- Reversing a string with `[::-1]`

## The idea

A **slice** takes a piece of a string. `s[start:stop]` gives the characters from `start` **up to but not including** `stop`.

```python
word = "BROADCAST"
#       012345678
print(word[0:5])    # BROAD
print(word[5:9])    # CAST
```

The length of the slice is `stop - start`.

## Leaving out start or stop

- No `start` means "from the beginning".
- No `stop` means "to the end".

```python
print(word[:5])     # BROAD
print(word[5:])     # CAST
print(word[:])      # BROADCAST (a full copy)
```

## Negative slices

Negative numbers count from the end, just like indexes:

```python
print(word[-4:])    # CAST  (last 4)
print(word[:-4])    # BROAD (all but the last 4)
print(word[-4:-1])  # CAS   (stop is still not included!)
```

## Steps

A third number sets the **step**: how many characters to jump each time.

```python
code = "a1b2c3"
print(code[::2])    # abc   (every 2nd, starting at 0)
print(code[1::2])   # 123   (every 2nd, starting at 1)
```

## Reversing

A step of `-1` walks backwards. `[::-1]` reverses the whole string:

```python
print("TRATS"[::-1])   # START
```

## Slices never crash

Unlike single indexes, slices that go past the end just stop at the end:

```python
print("HI"[0:10])    # HI
print("HI"[5:])      # ''  (empty string)
```

Check `len()` when a short string needs special handling.

## Common mistakes

- **Expecting `stop` to be included.** `s[0:5]` gives 5 characters: indexes 0 to 4.
- **Using `[-4:-1]` to get the last 4.** That stops before the last character. Use `[-4:]`.
- **Trying to assign to a slice.** Strings can't be changed; build a new one.
- **Mixing up start and step.** `[::2]` and `[1::2]` start in different places.
