import os
import logging
import argparse

import numpy as np
from scipy import ndimage

from spa import utils
import spa.volume

logger = logging.getLogger("SIZE ESTIMATION")

def estimate_particle_size(volume, threshold, kernel_size=3, kernel_spherical=True):
    volume_processed = volume

    # guassian blurr
    logger.info(f"Applying guassian filter...")
    volume_processed = ndimage.gaussian_filter(volume_processed, sigma=0.5, mode='constant', cval=0.0)

    # binary segmentation
    logger.info(f"Applying binary segmentation...")
    volume_processed = spa.volume.binary_segmentation(volume_processed, threshold, is_binary_mask=False)

    # topological operations
    if kernel_spherical:
        kernel = spa.volume.get_spherical_kernel(kernel_size)
    else:
        kernel = np.ones((kernel_size, kernel_size, kernel_size)).astype(bool)
    logger.info(f"Applying topological opening...")
    volume_processed = ndimage.binary_opening(volume_processed, structure=kernel)
    logger.info(f"Applying topological closing...")
    volume_processed = ndimage.binary_closing(volume_processed, structure=kernel)

    logger.info(f"Finding the enclosed sphere...")
    sphere = spa.volume.compute_enclosing_sphere(volume_processed)
    return sphere

if __name__ == "__main__":
    # python src/spa/analyses/size_estimation.py -v test_/input/volume/emd_0407_mask_aligned.mrc   -s --output-dir test_/output/
    # python src/spa/analyses/size_estimation.py -v test_/input/volume/emd_0407_volume_aligned.map -t 0.008 -s --output-dir test_/output/
    parser = argparse.ArgumentParser(
        description=(
            "Estimates the size of the positive density of a .mrc file, "
            "by finding the enclosing sphere of the binary segmented volume. \n"
            "Use --save to create a binary spherical mask (.mrc) for visual validation.\n"
            "Usage: \n"
            "\t python size_estimation.py -v test_/prot_mask_final.mrc -s\n"
            "\t python size_estimation.py -v test_/postprocess.mrc -t 0.0143 -s"
        ),
        formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("-v", "--volume",    type=str, required=True, help="Volume or Mask filepath (.mrc)")
    parser.add_argument("-t", "--threshold", type=float, default=0,   help="Threshold value that best filters out noise (default: 0)")
    parser.add_argument("-s", "--save",      action="store_true",     help="Save enclosing sphere as a mask file (.mrc)")
    parser = utils.cli.add_common_arguments(parser) # adds --verbose, --json, --output-dir --debug
    args = parser.parse_args()

    # directory creation
    basedir = utils.paths.mkdir_timestamp(args.output_dir) # skip if args.output_dir is None

    # logging
    utils.log.configure_logging(verbose=args.verbose, output_directory=basedir, capture_warnings=True)

    if basedir:
        logger.info(f"Output directory set to: {basedir}")

    # computation
    logger.info(f"Loading file: {args.volume}")
    volume   = spa.volume.mrc.load(args.volume)

    logger.info(f"Running size estimation...")
    result = estimate_particle_size(volume["data"], threshold=args.threshold)
    
    result["shape"] = volume["shape"][0]
    result["voxel_size_A_per_px"] = volume["voxel_size_A_per_px"][0]
    
    # save mask
    if args.save:
        fname = f"mask_r{int(result['radius'])}.mrc"
        fpath = os.path.join(basedir or ".", fname)
        logger.info(f"Saving mask to {fpath}")
        mask = spa.volume.create_spherical_mask(
                shape  = volume["data"].shape,
                radius = result["radius"],
                center = result["center"]
        )
        utils.mrc.save(volume=mask.astype(np.uint8), voxel_size=volume["voxel_size_A_per_px"], filename=fpath)
        result["mask_filepath"] = fpath

    # print and save output
    output = utils.output.print_and_save(result, 
                                         print_as="json" if args.json else "yaml",
                                         filepath=os.path.join(basedir, "size_estimation") if basedir else None)


