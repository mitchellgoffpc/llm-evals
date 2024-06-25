import difflib

UNIFIED_DIFF_SYSTEM_PROMPT = "You are an AI programming assistant. When asked to modify a file, you should write out the changes as a unified diff, similar to what `diff -U0` would produce. Make sure to include some context around each change so the patch can be applied correctly."

def unified_diff_strategy(original, response):
    original_lines = original.splitlines(keepends=True)
    patch_lines = response.splitlines(keepends=True)
    patched = original_lines[:]

    for patch in difflib.unified_diff(original_lines, patch_lines, n=0, lineterm=''):
        print(patch)
        if patch.startswith('+++') or patch.startswith('---') or patch.startswith('@@'):
            continue
        if patch.startswith('+'):
            patched.append(patch[1:])
        elif patch.startswith('-'):
            patched.remove(patch[1:])

    return ''.join(patched)


if __name__ == "__main__":
    import sys

    if len(sys.argv) != 3:
        print("Usage: python unified_diff.py <original_file> <patch>")
        sys.exit(1)

    with open(sys.argv[1], 'r') as f1, open(sys.argv[2], 'r') as f2:
        result = unified_diff_strategy(f1.read(), f2.read())
        # print(result)
