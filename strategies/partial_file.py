PARTIAL_FILE_SYSTEM_PROMPT = "You are an AI programming assistent. When asked to modify a file, you should return the file with the requested changes. If the file is very long and you want to leave some parts unchanged, add a line with [UNCHANGED] to denote that the code in between shouldn't be changed. Don't add comments like '... rest of the code remains unchanged', just get to a natural breaking point and then add an [UNCHANGED] and move onto the next section that you want to modify. Be sure to include some surrounding context in each section so I know where it's supposed to go."

def partial_file_strategy(original, response):
    return response


if __name__ == "__main__":
    import sys

    if len(sys.argv) != 3:
        print("Usage: python partial_file.py <original_file> <patch>")
        sys.exit(1)

    with open(sys.argv[1], 'r') as f1, open(sys.argv[2], 'r') as f2:
        result = partial_file_strategy(f1.read(), f2.read())
        print(result)
