import shlex
import logging
from pathlib import Path

import pandas as pd

__myname__ = Path(__file__).stem
logger = logging.getLogger(__myname__)

# reference: https://relion.readthedocs.io/en/release-3.1/Reference/Conventions.html#star-format

def read_table(filepath:str, table:str) -> pd.DataFrame:
    """
    Read one table of a STAR file (RELION) as a DataFrame.

    Parameters
    ----------
    filepath : str
        Path to the STAR file
    table : str
        Table name

    Returns
    -------
    pandas.DataFrame

    """
    block = "data_" + table.removeprefix("data_")
    labels, rows, pairs = [], [], {}
    found = in_loop = False

    with open(filepath) as file:
        for number, line in enumerate(file, start=1):
            words = shlex.split(line) if '"' in line else line.split() # RELION quotes empty values and values with spaces
            if not found:
                found = words == [block]                               # skip to data_<table>
            elif not words or words[0].startswith("#"):
                continue                                               # blank lines and comments ("# version 50001")
            elif len(words) == 1 and words[0].startswith("data_"):
                break                                                  # the next table starts
            elif words[0] == "loop_":
                in_loop = True
            elif words[0].startswith("_") and in_loop:
                labels.append(words[0][1:])                            # eg: "_rlnPipeLineEdgeToNode #2" -> "rlnPipeLineEdgeToNode"
            elif words[0].startswith("_"):
                pairs[words[0][1:]] = words[1]                         # eg: "_rlnPipeLineJobCounter 2"
            elif len(words) == len(labels):
                rows.append(words)
            else:                                                      # incomplete file
                raise ValueError(f"{filepath}, line {number}: {len(words)} values for {len(labels)} labels")

    if not found:
        logger.warning(f"{filepath}: no table {block}")
        return pd.DataFrame()
    if pairs:                                                          # one row for a table without loop_
        return pd.DataFrame([pairs])
    return pd.DataFrame(rows, columns=labels)
