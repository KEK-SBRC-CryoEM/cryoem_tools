import logging
import sys, os

def configure_logging(verbose=False, output_directory=None, capture_warnings=False):
    """
    Configure application-wide logging behavior.

    This function initializes the root logger. 
    Logs are emitted to stderr by default and 
        can optionally be written to a file.

    Parameters
    ----------
    verbose : bool, optional
        If True, set logging level to INFO. Otherwise, use WARNING level.
        Default is False.

    output_directory : str or None, optional
        Path to where the logs should also be written. If None, logs
        are only emitted to stderr. Default is None.

    capture_warnings : bool, optional
        If True, redirect Python warnings (from the warnings module)
        into the logging system. If False, warnings use the default
        behavior. Default is False.

    Notes
    -----
    This function should be called once at the application entry point
    (e.g., inside a `if __name__ == "__main__"` block). Library modules
    should not configure logging themselves, but instead obtain loggers
    using `logging.getLogger(__name__)`.

    Example
    -------
    >>> from utils import configure_logging
    >>> configure_logging(verbose=True, output_directory="results", capture_warnings=True)
    >>> logger = logging.getLogger(__name__)
    >>> logger.info("Logging initialized.")
    """
    level = logging.INFO if verbose else logging.WARNING

    handlers = []

    # terminal handler
    terminal_handler = logging.StreamHandler(sys.stderr)
    terminal_handler.setLevel(level)
    handlers.append(terminal_handler)

    # file handler
    if output_directory:
        log_file = os.path.join(output_directory, "run.log")
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(level)
        handlers.append(file_handler)

    # config
    logging.basicConfig(
        level=level,
        format="%(name)s | %(levelname)s: %(message)s",
        handlers=handlers,
        # force=True,
    )

    # redirect warning to the logger
    logging.captureWarnings(capture_warnings)