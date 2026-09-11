import argparse
import logging
import os

from spa import utils
from collections.abc import Mapping

def add_common_arguments(parser: argparse.ArgumentParser) -> argparse.ArgumentParser:
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
    parser.add_argument("-o", "--output-dir", type=str, help="Specify a directory to enable saving the output. If not provided, results print to stdout and logs to stderr only. If provided, a named subdirectory will be created under this specified directory. If it already exists, a unique suffix is appended (determined by --output-dir-suffix).")
    parser.add_argument("--output-dir-suffix", choices=["timestamp", "number"], default="timestamp", type=str, help="Determines the suffix appended to the output directory only if the output directory already exists. Choices: 'timestamp' (e.g., dir_2026-09-09_13-14-17) or 'number' (e.g., dir_001). Default: timestamp")    
    parser.add_argument("--verbose", action="store_true", help="Enable more detailed logging.")
    parser.add_argument("--debug",   action="store_true", help="May generate extra logs and data.")
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
    common = {k:args[k] for k in ["Debug", "Verbose", "Output Path"]} # "Output Dir Suffix" is shown implicitly
    common["Output Format"] = "JSON" if args["Json"] else "YAML"
    width  = max([len(k) for k in common.keys()])
    for key, value in common.items():
        logger.info(f"+ {key:<{width}}: {value}")
    logger.info(divider * divider_length)

    # scripts argument
    others = {k:v for k,v in args.items() if k not in ["Debug", "Verbose", "Output Format", "Output Dir", "Json", "Output Dir Suffix", "Output Path"]}
    if others:
        logger.info("Inputs:")
        width  = max([len(k) for k in others.keys()])
        
        for key, value in others.items():
            logger.info(f"+ {key:<{width}}: {value}")
        logger.info(divider * divider_length)
    
def init_cli(name:str, parser:argparse.ArgumentParser) -> argparse.Namespace:
    """
    Extend parser, create output directory, init logging, print header.

    Add --debug, --verbose, --json, --output-dir, --output-dir-suffix.
    
    Return parsed args with `output_path` set to the resolved run directory
    (None if --output-dir was not given).
    """
    parser = utils.cli.add_common_arguments(parser) # adds --debug --verbose --json --output-dir --output-dir-suffix
    args = parser.parse_args()

    # directory creation (extends args)
    args.output_path = utils.paths.mkdir_output(os.path.join(args.output_dir, name), mode=args.output_dir_suffix) # skip if args.output_dir is None

    # logging
    utils.log.configure_logging(verbose=args.verbose, output_directory=args.output_path, capture_warnings=True)

    # print log header
    if args.verbose:
        utils.cli.log_cli_header(logger=logging.getLogger(name), script_name=name, args=args)

    return args
