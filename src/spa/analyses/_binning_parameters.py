## temporary script for testing; need refactoring ##

import os
import logging
import argparse
from pathlib import Path

import numpy as np
from spa import utils

__myname__ = Path(__file__).stem
logger = logging.getLogger(__myname__)

if __name__ == "__main__":
    ########## CLI setup ##########
    parser = argparse.ArgumentParser()
    parser.add_argument("-p", "--pixel_size"       , type=float, required=True, help="Current Pixel Size")
    parser.add_argument("-b", "--box_size"         , type=float, required=True, help="Current Box Size")
    parser.add_argument("-t", "--target_pixel_size", type=float, required=True, help="Target Pixel Size")

    args = utils.cli.init_cli(__myname__, parser) # check the docstring for complete behavior; args.output_path is the resolved run directory
    ##### / #####

    # computation
    logger.info("Computing binning parameters...")
    # binned_box_size   = int(2 * ((args.box_size * args.pixel_size / args.target_pixel_size) // 2))
    binned_box_size   = int(2*np.ceil((args.box_size * args.pixel_size / args.target_pixel_size)/2))
    # adjusted_box_size = adjust_boxsize(binned_box_size, use_eman_boxsizes=True)
    factor            = args.box_size/binned_box_size
    binned_pixel_size = args.pixel_size * factor

    if args.target_pixel_size != binned_pixel_size:
        logger.info("+ Pixel size was adjusted to result in a even box size.")

    logger.info(f"+ Binned pixel size: {binned_pixel_size}")
    logger.info(f"+ Binned box size  : {binned_box_size}")
    logger.info(f"+ Binning factor   : {factor}")
    
    result = {"binned_pixel_size": binned_pixel_size,
              "binned_box_size"  : binned_box_size,
              "binning_factor"   : factor,}

    # print and save output
    output = utils.output.print_and_save(result, 
                                         print_as="json" if args.json else "yaml",
                                         filepath=os.path.join(args.output_path, __myname__) if args.output_path else None)
    logger.info(f"Result:\n{output['yaml']}")
    logger.info(f"Exiting...")
    logger.info("-"*40)