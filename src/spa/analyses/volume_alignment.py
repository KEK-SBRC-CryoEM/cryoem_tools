

import os
import logging
import argparse
from pathlib import Path

from spa import utils
from spa import volume as volops
from spa.visualization import volume as visvol 

__myname__ = Path(__file__).stem
logger = logging.getLogger(__myname__)

def generate_figures(segmented, initial_sphere, aligned_sphere, output_path):
    # define sphere coloring
    initial_sphere["plot"] = {"color": (255, 0, 0), "alpha": 1}
    aligned_sphere["plot"] = {"color": (0, 255, 0), "alpha": 1}

    #
    slices     = volops.get_orthogonal_slices(segmented)
    imgs_gray  = [visvol.normalize_to_uint8(img, max_value=1) for img in slices]
    visvol.show_slices(imgs_gray, spheres=[initial_sphere, aligned_sphere], 
                title="Aligned and Centered Volume (Orthogonal Slices)", 
                output_path=output_path)

def do_alignment(volume, mask, threshold):
    # 1. segmentation if mask is not provided
    segmented = mask
    if mask is None:
        logger.info("Segmenting volume...")
        segmented = volops.binary_segmentation(volume, threshold, is_binary_mask=False)

    # 2. center of the volume
    logger.info("Computing the enclosing sphere...")
    initial_enclosing_sphere = volops.compute_enclosing_sphere(segmented)

    # 3. pca alignment
    logger.info("Aligning...")
    alignment_data = volops.covariance_alignment(binary_mask=segmented, 
                                                 center=initial_enclosing_sphere["center"], 
                                                 volume=volume,
                                                 center_mode="box")

    alignment_data["initial_enclosing_sphere"] = initial_enclosing_sphere
    alignment_data["aligned_enclosing_sphere"] = volops.compute_enclosing_sphere(alignment_data["mask"])

    return alignment_data

if __name__ == "__main__":
    # python src/spa/analyses/volume_alignment.py -v volume.mrc -m mask.mrc -s
    # python src/spa/analyses/volume_alignment.py -v volume.mrc -t 0.01 -s
    parser = argparse.ArgumentParser(
        description=(
            "Align a 3D volume/mask to the orthogonal axes. "
            "Calculate the rotation using Principal Component Analysis (PCA) "
                "to orient the longest view of the structure along a primary axis and "
                "center it within the coordinate box."
            "User provides the volume to be aligned and threshold for binary segmentation OR a binary mask."
            
            "Usage: \n"
            "\t python volume_alignment.py -v volume.mrc -m mask.mrc -s\n"
            "\t python volume_alignment.py -v volume.mrc -t 0.01 -s"
        ),
        formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("-v", "--volume",    type=str, required=True, help="Volume filepath (.mrc)")
    parser.add_argument("-m", "--mask",      type=str,                help="Mask filepath (.mrc)")
    parser.add_argument("-t", "--threshold", type=float, default=0,   help="Threshold for binary segmentation (default: 0).")
    parser.add_argument("-s", "--save",      action="store_true",     help="Save orthogonal slices of the aligned volume. (.png)")
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
    logger.info("Loading volume...")
    volume_mrc = utils.mrc.load(args.volume)
    volume     = volume_mrc["data"]
    voxel_size = volume_mrc["voxel_size_A_per_px"]
    
    mask = None
    if args.mask:
        logger.info("Loading mask...")
        mask = utils.mrc.load(args.mask)["data"]
        logger.info(f"+ Binary Mask? {volops.is_binary(mask)}")

    logger.info(f"Running alignment...")
    alignment_data = do_alignment(volume, mask, args.threshold)
    alignment_data["box_size"] = alignment_data["volume"].shape[0]

    # saving aligned volume
    avolume_path = os.path.join(basedir or ".", f"aligned_{Path(args.volume).name}")
    amask_path   = os.path.join(basedir or ".", f"aligned_{Path(args.mask).name}") if args.mask else None

    utils.mrc.save(volume     = alignment_data["volume"],
                   voxel_size = voxel_size,
                   filename   = avolume_path)
    if amask_path:
        utils.mrc.save(volume     = alignment_data["mask"],
                       voxel_size = voxel_size,
                       filename   = amask_path)

    # figures
    if args.save:
        logger.info("Generating figures...")
        outp = os.path.join(basedir or ".", "orthogonal_view.png")
        generate_figures(segmented      = alignment_data["mask"],
                         initial_sphere = alignment_data["initial_enclosing_sphere"], 
                         aligned_sphere = alignment_data["aligned_enclosing_sphere"], 
                         output_path    = outp)
        logger.info(f"+ saved to {outp}")

    # print and save output
    ## replacing volume and mask data by its path
    alignment_data["volume"] = avolume_path
    alignment_data["mask"]   = amask_path
    output = utils.output.print_and_save(alignment_data, 
                                        print_as="json" if args.json else "yaml",
                                        filepath=os.path.join(basedir, __myname__) if basedir else None)
    
    logger.info(f"Result:\n{output['yaml']}")
    logger.info(f"Exiting...")
    logger.info("-"*40)
