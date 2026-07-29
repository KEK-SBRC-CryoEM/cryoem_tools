import argparse

def add_common_arguments(parser):
    """
    Add shared command-line arguments related to input/output behavior.

    This function extends an existing ``argparse.ArgumentParser`` with
    standardized flags used across scripts in the project. 
    
    Example
    -------
    >>> parser = argparse.ArgumentParser()
    >>> parser.add_argument(...)
    >>> add_common_cli_arguments(parser)
    >>> args = parser.parse_args()
    """
    parser.add_argument("--json", action="store_true", help="Output results as JSON. Useful for the automation pipeline. If not provided, output will be shown in YAML, a human-friendly format.")
    parser.add_argument("--output-dir", type=str, help="Directory path where all outputs and logs will be saved. If not provided, results are printed to stdout and logs to stderr only.")
    parser.add_argument("--verbose", action="store_true", help="Enable more detailed logging.")
    parser.add_argument("--debug", action="store_true", help="May generate extra logs and data.")
    return parser

