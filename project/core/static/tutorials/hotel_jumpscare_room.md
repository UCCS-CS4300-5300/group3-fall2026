# Jumpscare: The Mail Carrier

**The Hotel · Dictionaries / Maps · Jump Scare**

> The mail bag drops to the floor. The carrier who dropped it is still standing, swaying, and turning toward you.

## What's happening

The code should update a mail bag dictionary and print what's inside, but it uses the wrong key names and the wrong tools, and it crashes when it asks for something that isn't there.

## How to debug fast

1. **Read the error.** `KeyError: 'X'` means that exact key isn't in the dictionary. `AttributeError` means you called a method dictionaries don't have.
2. **Print the dictionary** and compare its keys, letter for letter, with the ones in the code.

## Bugs to look for

- **Case-sensitive keys.** `"Mail"` and `"mail"` are different keys.
- **Wrong method.** Dictionaries have no `.add()`. To add or set a key, assign it: `d["key"] = value`.
- **Missing keys.** `d["key"]` crashes if the key isn't there. `.get("key", 0)` returns a default instead.

```python
bag = {"letters": 4}
bag["parcels"] = 2               # add a key
print(bag.get("stamps", 0))      # 0, no crash
```

## Checklist

- Do all the keys match exactly?
- Is every new key added with `d[key] = value`?
- Does the missing item print a default instead of crashing?
