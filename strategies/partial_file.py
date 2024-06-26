import difflib

PARTIAL_FILE_SYSTEM_PROMPT = "You are an AI programming assistent. When asked to modify a file, you should return the file with the requested changes. If the file is very long and you want to leave some parts unchanged, add a line with [UNCHANGED] to denote that the code in between shouldn't be changed. Don't add comments like '... rest of the code remains unchanged', just get to a natural breaking point and then add an [UNCHANGED] and move onto the next section that you want to modify. Be sure to include some surrounding context in each section so I know where it's supposed to go."

def partial_file_strategy(original, response):
    original_lines = original.splitlines(keepends=True)
    response_sections = response.split('[UNCHANGED]')
    output_lines = []
    start_idx = 0

    for section in response_sections:
        section = section.lstrip('\n')
        if not section.strip():
            continue
        section_lines = section.splitlines(keepends=True)

        matcher = difflib.SequenceMatcher(None, original_lines[start_idx:], section_lines)
        ops = matcher.get_opcodes()
        new_start_idx = start_idx
        for i, (tag, alo, ahi, blo, bhi) in enumerate(ops):
            if i == 0 and tag == 'delete':
                output_lines.extend(original_lines[start_idx+alo:start_idx+ahi])
            elif tag in ('insert', 'replace', 'equal'):
                output_lines.extend(section_lines[blo:bhi])
                new_start_idx = start_idx + ahi

        start_idx = new_start_idx

    if response_sections and not response_sections[-1].strip():  # Ends with an [UNCHANGED]
        output_lines.extend(original_lines[start_idx:])
    return ''.join(output_lines)


if __name__ == "__main__":
    import sys

    if len(sys.argv) != 4:
        print("Usage: python partial_file.py <original_file> <expected_file> <patch>")
        sys.exit(1)

    with open(sys.argv[1]) as f1, open(sys.argv[2]) as f2, open(sys.argv[3]) as f3:
        original = f1.read()
        expected = f2.read()
        patch = f3.read()

    result = partial_file_strategy(original, patch)
    diff = difflib.unified_diff(
        expected.splitlines(keepends=True),
        result.splitlines(keepends=True),
        fromfile='original',
        tofile='modified',
        lineterm=''
    )
    for line in diff:
        print(line, end='')
