WHOLE_FILE_SYSTEM_PROMPT = "You are an AI programming assistant. When asked to modify a file, you should return the entire file with the requested changes, with nothing omitted. Even if the file is very long, you must return the entire thing, and not skip anything."

def whole_file_strategy(original, response):
    return response
