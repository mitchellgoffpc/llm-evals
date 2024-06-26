#!/usr/bin/env python3
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
from strategies.partial_file import PARTIAL_FILE_SYSTEM_PROMPT, partial_file_strategy

# ANSI color codes
RED = '\033[91m'
GREEN = '\033[92m'
YELLOW = '\033[93m'
RESET = '\033[0m'

MODEL_SHORTCUTS = {s: model for model in MODELS for s in [model.name, *model.shortcuts]}
STRATEGIES = {
    'wholefile': (WHOLE_FILE_SYSTEM_PROMPT, whole_file_strategy),
    'udiff': (UNIFIED_DIFF_SYSTEM_PROMPT, unified_diff_strategy),
    'partfile': (PARTIAL_FILE_SYSTEM_PROMPT, partial_file_strategy),
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

def run_tests(model, strategy, tests_to_run=None, dump=False):
    data_dir = Path(__file__).parent / 'tests'
    if not data_dir.exists():
        print(f"Error: '{data_dir}' directory not found.")
        sys.exit(1)

    test_suites = [d for d in data_dir.iterdir() if d.is_dir()]
    if not test_suites:
        print(f"No test suites found in '{data_dir}' directory.")
        sys.exit(1)

    system_prompt, apply_patch = STRATEGIES[strategy]
    total_tests = 0
    passed_tests = 0

    for test_suite in test_suites:
        tests_file = test_suite / 'tests.json'
        if not tests_file.exists():
            raise RuntimeError(f"Test suite '{test_suite.name}' is missing tests.json file.")

        test_configs = json.loads(tests_file.read_text())
        for test_name, test_config in test_configs.items():
            full_test_name = f"{test_suite.name}.{test_name}"
            if tests_to_run and test_suite.name not in tests_to_run and full_test_name not in tests_to_run:
                continue

            input_file = test_suite / test_config['input']
            output_file = test_suite / test_config['output']

            if not input_file.exists():
                raise RuntimeError(f"Test suite '{test_suite.name}' is missing input file '{input_file.name}'.")
            if not output_file.exists():
                raise RuntimeError(f"Test suite '{test_suite.name}' is missing output file '{output_file.name}'.")

            input_content = input_file.read_text().strip()
            output_content = output_file.read_text().strip()
            total_tests += 1

            prompt = f"```\n{input_content}\n```\n\n{test_config['prompt']}"
            response = ''.join(query(prompt, model, system_prompt=system_prompt))
            patch = extract_code_block(response)
            result = apply_patch(input_content, patch)

            if dump:
                dump_dir = Path('/tmp/model_dump') / test_suite.name
                dump_dir.mkdir(parents=True, exist_ok=True)
                (dump_dir / f'raw_{test_name}').write_text(response)
                (dump_dir / f'patch_{test_name}').write_text(patch)
                (dump_dir / f'result_{test_name}').write_text(result)

            if result == output_content:
                print(f"{GREEN}Test {full_test_name} passed.{RESET}")
                passed_tests += 1
            else:
                print(f"{RED}Test {full_test_name} failed.{RESET}")
                print_diff(output_content, result, output_file.name, 'model_response')

    print(f"\nTest Results: {passed_tests}/{total_tests} passed")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run tests against a given LLM.")
    parser.add_argument('-m', '--model', choices=MODEL_SHORTCUTS.keys(), help="Name or shortcut of the model to use")
    parser.add_argument('-s', '--strategy', choices=STRATEGIES.keys(), default='partfile', help="Strategy to process model response")
    parser.add_argument('--dump', action='store_true', help="Dump raw model responses to output files")
    parser.add_argument('tests', nargs='*', help="Names of specific tests to run (e.g., test_suite.test_name)")
    args = parser.parse_args()

    run_tests(MODEL_SHORTCUTS[args.model], args.strategy, args.tests, args.dump)
