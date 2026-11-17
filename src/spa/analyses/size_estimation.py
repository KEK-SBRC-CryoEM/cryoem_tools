import os
import logging
import argparse
from pathlib import Path

import numpy as np
from scipy import ndimage

from spa import utils
from spa import volume as volops

__myname__ = Path(__file__).stem
logger = logging.getLogger(__myname__)

def estimate_particle_size(volume, threshold, kernel_size=3, kernel_spherical=True):
    volume_processed = volume

    # guassian blurr
    logger.info(f"Applying guassian filter...")
    volume_processed = ndimage.gaussian_filter(volume_processed, sigma=0.5, mode='constant', cval=0.0)

    # binary segmentation
    logger.info(f"Applying binary segmentation...")
    volume_processed = volops.binary_segmentation(volume_processed, threshold, is_binary_mask=False)

    # topological operations
    if kernel_spherical:
        kernel = volops.get_spherical_kernel(kernel_size)
    else:
        kernel = np.ones((kernel_size, kernel_size, kernel_size)).astype(bool)
    logger.info(f"Applying topological opening...")
    volume_processed = ndimage.binary_opening(volume_processed, structure=kernel)
    logger.info(f"Applying topological closing...")
    volume_processed = ndimage.binary_closing(volume_processed, structure=kernel)

    logger.info(f"Finding the enclosed sphere...")
    coords = volops.get_coordinates(volume_processed)
    sphere = volops.compute_enclosing_sphere(coords)

    result = {"center_zyx_px": sphere["center"],
              "radius_px"    : sphere["radius"],
              "diameter_px"  : sphere["diameter"]
    }

    return result

def run(volume, threshold, pixel_size_A_per_px):
    # 1. enclosing sphere of the segmented volume in pixels
    sphere = estimate_particle_size(volume, threshold)

    # 2. output organization
    values = {"center_zyx_px": sphere["center_zyx_px"],
              "radius_px"    : sphere["radius_px"],
              "diameter_px"  : sphere["diameter_px"],
              "radius_A"     : sphere["radius_px"]   * pixel_size_A_per_px,
              "diameter_A"   : sphere["diameter_px"] * pixel_size_A_per_px}

    data   = {} 
    return values, data

if __name__ == "__main__":
    ### 1. CLI setup ###
    parser = argparse.ArgumentParser(
        description=(
            "Estimate the size of the positive density of a .mrc file, "
            "by finding the enclosing sphere of the binary segmented volume. \n"
            "Use --save to create a binary spherical mask (.mrc) for visual validation.\n"
            "Usage: \n"
            "\t python size_estimation.py -v test_/prot_mask_final.mrc -s\n"
            "\t python size_estimation.py -v test_/postprocess.mrc -t 0.0143 -s"
        ),
        formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("-v", "--volume",    type=str, required=True, help="Volume or Mask filepath (.mrc)")
    parser.add_argument("-t", "--threshold", type=float, default=0,   help="Threshold value that best filters out noise (default: 0). Not required if --volume is a mask.")
    parser.add_argument("-s", "--save",      action="store_true",     help="Save enclosing sphere as a mask file (.mrc)")

    args = utils.cli.init_cli(__myname__, parser) # check the docstring for complete behavior; args.output_path is the resolved run directory

    ### 2. I/O DEFINITION ###
    inputs  = {"volume_filepath"    : args.volume,
               "threshold"          : args.threshold,
               "box_size_px"        : ..., # from the volume header
               "pixel_size_A_per_px": ..., # from the volume header
    }
    outputs = {"center_zyx_px": ...,  # sphere center, as array indices (z, y, x)
               "radius_px"    : ...,
               "diameter_px"  : ...,
               "radius_A"     : ...,
               "diameter_A"   : ...,  # the particle size
               "mask_filepath": None, # only when --save
    }

    ### 3. PREPROCESSING ###
    logger.info(f"Loading file: {inputs['volume_filepath']}")
    volume_mrc = utils.mrc.load(inputs["volume_filepath"])
    volume     = volume_mrc["data"]
    inputs["box_size_px"]         = volume.shape[0]
    inputs["pixel_size_A_per_px"] = volume_mrc["voxel_size_A_per_px"][0]

    ### 4. MAIN ###
    logger.info("Running size estimation...")
    values, _ = run(volume, inputs["threshold"], inputs["pixel_size_A_per_px"])
    outputs.update(values)

    ### 5. POSTPROCESSING ###
    # save the enclosing sphere as a mask
    if args.save:
        outputs["mask_filepath"] = os.path.join(args.output_path or ".", f"spherical_mask.mrc")
        logger.info(f"Saving mask to {outputs['mask_filepath']}")
        mask = volops.create_spherical_mask(shape  = volume.shape,
                                            radius = outputs["radius_px"],
                                            center = outputs["center_zyx_px"])
        utils.mrc.save(volume     = mask.astype(np.uint8),
                       voxel_size = volume_mrc["voxel_size_A_per_px"],
                       filename   = outputs["mask_filepath"])
    
    # save I/O
    utils.output.print_and_save({"input":inputs, "output":outputs},
                                print_as="json" if args.json else "yaml",
                                filepath=os.path.join(args.output_path, __myname__) if args.output_path else None)
    logger.info("Exiting...")
    logger.info("-"*40)
    


