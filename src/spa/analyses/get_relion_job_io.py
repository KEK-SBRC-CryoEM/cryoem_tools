import os
import logging
import argparse
from fnmatch import fnmatch
from pathlib import Path

import pandas as pd
from spa import utils

__myname__ = Path(__file__).stem
logger = logging.getLogger(__myname__)

def run(processes:pd.DataFrame, input_edges:pd.DataFrame, output_edges:pd.DataFrame, job_dir:Path, match:str|None=None) -> tuple[dict, dict]:
    job     = processes.iloc[0]
    input_nodes  = list(input_edges.get("rlnPipeLineEdgeFromNode", []))
    output_nodes = list(output_edges.get("rlnPipeLineEdgeToNode", []))

    if match:
        matched = [path for path in output_nodes if fnmatch(Path(path).name, match)]
        if not matched:
            raise ValueError(f"no output matches {match!r}: {', '.join(Path(path).name for path in output_nodes)}")
        output_nodes = matched

    values = {"process"     : job.get("rlnPipeLineProcessName"),
              "type"        : job.get("rlnPipeLineProcessTypeLabel"),
              "input_nodes" : input_nodes,
              "output_nodes": output_nodes}
    data   = {}
    return values, data

if __name__ == "__main__":
    ### 1. CLI setup ###
    parser = argparse.ArgumentParser(
        description=(
            "List the job, input files and output files of a RELION job, from its job_pipeline.star.\n"
            "Run it from the RELION project folder: paths are relative to it, as RELION writes them.\n"
            "Use --match to keep only some outputs, e.g. the class maps.\n"
            "Usage: \n"
            "\t python relion_job_io.py -f InitialModel/job019/job_pipeline.star\n"
            "\t python relion_job_io.py -f InitialModel/job019/job_pipeline.star --match '*_class*.mrc'"
        ),
        formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("-f", "--filepath", type=str, required=True, help="The job_pipeline.star in a RELION job folder")
    parser.add_argument("--match",          type=str, default=None,  help="Keep the outputs whose file name matches this pattern, e.g. '*_class*.mrc' (default: all)")

    args = utils.cli.init_cli(__myname__, parser) # check the docstring for complete behavior; args.output_path is the resolved run directory

    ### 2. I/O DEFINITION ###
    inputs  = {"job_pipeline_filepath": args.filepath,
               "match"                : args.match,
    }
    outputs = {"process"     : ..., # the job, e.g. "InitialModel/job019/"
               "type"        : ..., # e.g. "relion.initialmodel"
               "input_nodes" : ..., # files the job read
               "output_nodes": ..., # files the job wrote, those matching --match
    }

    ### 3. PREPROCESSING ###
    logger.info(f"Reading file: {inputs['job_pipeline_filepath']}")
    processes_df    = utils.star.read_table(inputs["job_pipeline_filepath"], "pipeline_processes")
    input_edges_df  = utils.star.read_table(inputs["job_pipeline_filepath"], "pipeline_input_edges")
    output_edges_df = utils.star.read_table(inputs["job_pipeline_filepath"], "pipeline_output_edges")
    job_dir          = Path(inputs["job_pipeline_filepath"]).resolve().parent

    ### 4. MAIN ###
    logger.info("Listing the job's files...")
    values, _ = run(processes_df, input_edges_df, output_edges_df, job_dir, inputs["match"])
    outputs.update(values)

    ### 5. POSTPROCESSING ###
    # save I/O
    utils.output.print_and_save({"input":inputs, "output":outputs},
                                print_as="json" if args.json else "yaml",
                                filepath=os.path.join(args.output_path, __myname__) if args.output_path else None)
    logger.info("Exiting...")
    logger.info("-"*40)