from pathlib import Path

file = Path("core/exceptions.py")

text = file.read_text(encoding="utf-8")
lines = text.split("\n")

fixed = []
blank_count = 0

for line in lines:
    if line.strip() == "":
        blank_count += 1
    else:
        blank_count = 0

    # allow max 1 blank line
    if blank_count <= 1:
        fixed.append(line)

file.write_text("\n".join(fixed), encoding="utf-8")

print("✓ Fixed excessive blank lines in core/exceptions.py")
