import re
import sys
import json
import argparse
import difflib
from pathlib import Path
from ask.query import query
from ask.models import MODELS
from strategies.whole_file import WHOLE_FILE_SYSTEM_PROMPT, whole_file_strategy
from strategies.unified_diff import UNIFIED_DIFF_SYSTEM_PROMPT, unified_diff_strategy

# ANSI color codes
RED = '\033[91m'
GREEN = '\033[92m'
YELLOW = '\033[93m'
RESET = '\033[0m'

MODEL_SHORTCUTS = {s: model for model in MODELS for s in [model.name, *model.shortcuts]}
STRATEGIES = {
    'whole_file': (WHOLE_FILE_SYSTEM_PROMPT, whole_file_strategy),
    'unified_diff': (UNIFIED_DIFF_SYSTEM_PROMPT, unified_diff_strategy)
}

def print_diff(expected, actual, from_file, to_file):
    expected_lines = expected.splitlines(keepends=True)
    actual_lines = actual.splitlines(keepends=True)
    diff = difflib.unified_diff(expected_lines, actual_lines, fromfile=from_file, tofile=to_file, n=3)

    for line in diff:
        if line.startswith('+'):
            print(f"{GREEN}{line}{RESET}", end='')
        elif line.startswith('-'):
            print(f"{RED}{line}{RESET}", end='')
        elif line.startswith('^'):
            print(f"{YELLOW}{line}{RESET}", end='')
        else:
            print(line, end='')

def extract_code_block(text):
    pattern = r'```(?:\w+)?\n(.*?)\n```'
    match = re.search(pattern, text, re.DOTALL)
    if match:
        return match.group(1).strip()
    return text.strip()

def run_tests(model, strategy, test_cases_to_run=None):
    data_dir = Path(__file__).parent / 'test-cases'
    if not data_dir.exists():
        print(f"Error: '{data_dir}' directory not found.")
        sys.exit(1)

    test_cases = [d for d in data_dir.iterdir() if d.is_dir()]
    if not test_cases:
        print(f"No test cases found in '{data_dir}' directory.")
        sys.exit(1)

    # Filter test cases based on provided names
    if test_cases_to_run:
        test_cases = [tc for tc in test_cases if tc.name in test_cases_to_run]
        if not test_cases:
            print(f"No matching test cases found for the provided names.")
            sys.exit(1)

    system_prompt, process_response = STRATEGIES[strategy]
    total_tests = 0
    passed_tests = 0

    for test_case in test_cases:
        input_file = test_case / 'input'
        prompts_file = test_case / 'prompts.json'
        output_files = sorted(test_case.glob('output_*'))

        if not input_file.exists():
            raise RuntimeError(f"Test case '{test_case.name}' is missing input file.")
        if not prompts_file.exists():
            raise RuntimeError(f"Test case '{test_case.name}' is missing prompts.json file.")
        if not output_files:
            raise RuntimeError(f"Test case '{test_case.name}' has no output files.")

        input_content = input_file.read_text().strip()
        prompts = json.loads(prompts_file.read_text())

        for output_file in output_files:
            total_tests += 1
            output_name = output_file.name.removeprefix('output_')
            output_content = output_file.read_text().strip()

            # Get the prompt for the current output
            prompt = prompts.get(output_name)
            if not prompt:
                raise ValueError(f"No prompt found for test {test_case.name}.{output_name}")

            prompt = f"```\n{input_content}\n```\n\n{prompt}"
            response = ''.join(query(prompt, model))
            response = extract_code_block(response)
            response = process_response(input_content, response)

            if response == output_content:
                print(f"{GREEN}Test case {test_case.name}.{output_name} passed.{RESET}")
                passed_tests += 1
            else:
                print(f"{RED}Test case {test_case.name}.{output_name} failed.{RESET}")
                print_diff(output_content, response, output_file.name, 'model_response')

    print(f"\nTest Results: {passed_tests}/{total_tests} passed")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run test cases for the project.")
    parser.add_argument('-m', '--model', choices=MODEL_SHORTCUTS.keys(), help="Name or shortcut of the model to use")
    parser.add_argument('-s', '--strategy', choices=STRATEGIES.keys(), default='whole_file', help="Strategy to process model response")
    parser.add_argument('test_cases', nargs='*', help="Names of specific test cases to run")
    args = parser.parse_args()

    run_tests(MODEL_SHORTCUTS[args.model], args.strategy, args.test_cases)
