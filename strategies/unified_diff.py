UNIFIED_DIFF_SYSTEM_PROMPT = "You are an AI programming assistant. When asked to modify a file, you should write out the changes as a unified diff, similar to what `diff -U0` would produce. Make sure to include some context around each change so the patch can be applied correctly."

def unified_diff_strategy(original, response):
    return response
