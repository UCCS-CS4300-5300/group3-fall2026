def was_zombie_punched(program):
    if not program.strip():
        return {"reason": "Your program has no blocks yet.", "punched": False}
    open_ifs = []  # (indent, condition is true) for each if we're inside
    for line in program.splitlines():
        block = line.strip()
        if not block:
            continue
        indent = len(line) - len(line.lstrip())
        while open_ifs and open_ifs[-1][0] >= indent:
            open_ifs.pop()
        runs = all(is_true for _, is_true in open_ifs)
        if block == "punch zombie" and runs:
            return {"reason": "Your punch zombie block ran, so the zombie got knocked out!", "punched": True}
        if block.startswith("if"):
            open_ifs.append((indent, block == "if zombie"))
    if "if (empty)" in program:
        return {"reason": "Your if block needs the zombie block plugged into it.", "punched": False}
    return {"reason": "No punch zombie block ran. Put one inside your if zombie block.", "punched": False}
