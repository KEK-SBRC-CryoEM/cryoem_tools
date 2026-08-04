import os
import logging
import argparse
from pathlib import Path

from spa import utils
from spa import box
from spa import extraction

## STOPPED HERE

__myname__ = Path(__file__).stem
logger = logging.getLogger(__myname__)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description=(
            "Compute the Extraction and Rescaled box sizes required for the Relion Extraction job."
        ),
        formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("-f", "--binning_factor"     , type=float, required=True, help="Binning Factor: reference_box / binned_box")
    parser.add_argument("-t", "--target_rescaled_box", type=float, required=True, help="Target rescaled box: from the ctf limit")
    parser = utils.cli.add_common_arguments(parser) # adds --verbose, --json, --output-dir --debug
    args = parser.parse_args()

    # directory creation
    basedir = utils.paths.mkdir_timestamp(args.output_dir) # skip if args.output_dir is None

    # logging
    utils.log.configure_logging(verbose=args.verbose, output_directory=basedir, capture_warnings=True)

    # print log header
    if args.verbose:
        utils.cli.log_cli_header(logger=logger, script_name=__myname__, args=args)

    # computation
    logger.info("Computing extraction boxes...")
    result = extraction.parameters.compute_boxes(target_rescaled_box=args.target_rescaled_box,
                                                         binning_factor=args.binning_factor,
                                                         boxsize_list=box.FFT_FRIENDLY_SIZES)

    if args.target_rescaled_box != result["rescaled_box"]:
        logger.info("+ Rescaled box had to be adjusted!")

    logger.info(f"+ Rescaled box: {result['rescaled_box']}")
    logger.info(f"+ Extract  box: {result['extract_box']}")
    
    # print and save output
    output = utils.output.print_and_save(result, 
                                         print_as="json" if args.json else "yaml",
                                         filepath=os.path.join(basedir, __myname__) if basedir else None)
    logger.info(f"Result:\n{output['yaml']}")
    logger.info(f"Exiting...")
    logger.info("-"*40)
