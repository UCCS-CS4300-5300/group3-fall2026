# Jumpscare: The Night DJ

**The Radio Station · Strings · Jump Scare**

> The on-air light snaps on. The DJ in the booth turns around, and its headphones are the only thing holding its head together.

## What's happening

The code should pull the first and last words out of a distress message and send a corrected message. Two slices are off, and one line tries to do something strings can't do.

## How to debug fast

1. **Read the error.** A `TypeError` about "item assignment" means the code tried to change a string in place.
2. **Count the characters.** Write the indexes above the message. Slices stop **before** `stop`.
3. **Print each slice** to see exactly what you're getting.

## Bugs to look for

- **A slice one character short.** `s[0:5]` gives indexes 0 to 4. Does the word have 5 characters or 6?
- **The wrong way to get the end.** `s[-4:-1]` stops before the last character. Leave out `stop` to go all the way.
- **Changing a string in place.** Strings are immutable. Build a new string from pieces instead, using `+` and a slice.

```python
s = "HELLO WORLD"
s = "BYE" + s[5:]     # build a new string
print(s)              # BYE WORLD
```

## Checklist

- Do both words come out complete?
- Does the code run without a `TypeError`?
- Does the final message read correctly?
