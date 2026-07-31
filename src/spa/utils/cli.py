import argparse
import logging
from collections.abc import Mapping

def add_common_arguments(parser: argparse.ArgumentParser):
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

def _format_namespace(namespace):
    """ Helper to make the variable names printable and convert namespace to dict."""
    return {k.replace("_", " ").title():v for k,v in vars(namespace).items()}

def log_cli_header(logger        : logging.Logger,
                   script_name   : str,
                   args          : argparse.Namespace,
                   divider       : str = "-",
                   divider_length: int = 40) -> None:
    """Log CLI header."""
    
    # preparation
    args         = _format_namespace(args) # pretty-fy and convert to dict

    # script name
    logger.info(script_name.upper())

    # common arguments from add_common_arguments
    common = {k:args[k] for k in ["Debug", "Verbose", "Output Dir"]}
    common["Output Format"] = "JSON" if args["Json"] else "YAML"
    width  = max([len(k) for k in common.keys()])
    for key, value in common.items():
        logger.info(f"+ {key:<{width}}: {value}")
    logger.info(divider * divider_length)

    # scripts argument
    logger.info("Inputs:")
    others = {k:v for k,v in args.items() if k not in ["Debug", "Verbose", "Output Format", "Output Dir", "Json"]}
    width  = max([len(k) for k in others.keys()])
    for key, value in others.items():
        logger.info(f"+ {key:<{width}}: {value}")
    logger.info(divider * divider_length)
    
