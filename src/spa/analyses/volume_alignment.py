import os
import logging
import argparse
from pathlib import Path
from matplotlib import pyplot as plt

from spa import utils
from spa import volume as volops
from spa.visualization import volume as visvol 

__myname__ = Path(__file__).stem
logger = logging.getLogger(__myname__)

def generate_figures(original_segmented, aligned_segmented, output_path, titles=None):
    # reference
    initial_sphere = volops.compute_enclosing_sphere(volops.get_coordinates(original_segmented))
    aligned_sphere = volops.compute_enclosing_sphere(volops.get_coordinates(aligned_segmented))
    initial_sphere["plot"] = {"color": (255, 0, 0), "alpha": 1}
    aligned_sphere["plot"] = {"color": (0, 255, 0), "alpha": 1}

    slices_list = [volops.get_max_projection(seg) for seg in (original_segmented, aligned_segmented)]
    maxv = max(img.max() for slices in slices_list for img in slices)
    minv = min(img.min() for slices in slices_list for img in slices)

    plt.close('all')
    fig = plt.figure(figsize=(12, 8), layout="constrained")
    sm  = plt.cm.ScalarMappable(cmap='gray', norm=plt.Normalize(vmin=0, vmax=255))
    for subfig, slices, row_title in zip(fig.subfigures(2, 1), slices_list, titles):
        axs = subfig.subplots(1, 3)
        imgs_gray = [visvol.normalize_to_uint8(img, max_value=maxv, min_value=minv) for img in slices]
        visvol.show_slices(imgs_gray, spheres=[initial_sphere, aligned_sphere], axs=axs)
        subfig.suptitle(row_title, fontsize=12)
        subfig.colorbar(sm, ax=axs, orientation='vertical', fraction=0.02, pad=0.04)

    fig.savefig(output_path, dpi=300, bbox_inches='tight')

    return fig

def run(volume, mask, threshold):
    # 1. segmentation if mask is not provided
    segmented = mask
    if mask is None:
        logger.info("Segmenting volume...")
        segmented = volops.binary_segmentation(volume, threshold, is_binary_mask=False)

    # 2. pca alignment
    logger.info("Aligning...")
    alignment_data = volops.covariance_alignment(volume=volume,
                                                 binary_mask=segmented, 
                                                 center_mode="sphere",
                                                 order=0)

    # 3. output organization
    values = {"center_zyx_px"          : alignment_data["offset"],
              "rotation_zyx"           : alignment_data["rotation"],
              "principal_variances_px2": alignment_data["eigvals"],
              "skewness"               : alignment_data["skewness"]}
    
    data   = {"aligned_volume": alignment_data["volume"],
              "aligned_mask"  : alignment_data["mask"]}

    return values, data

if __name__ == "__main__":
    # python src/spa/analyses/volume_alignment.py -v volume.mrc -m mask.mrc -s
    # python src/spa/analyses/volume_alignment.py -v volume.mrc -t 0.01 -s

    ### 1. CLI setup ###
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
    
    args = utils.cli.init_cli(__myname__, parser) # check the docstring for complete behavior; args.output_path is the resolved run directory

    ### 2. I/O DEFINITION ###
    inputs  = {"volume_filepath"    : args.volume,
               "mask_filepath"      : args.mask,
               "threshold"          : None if args.mask else args.threshold, # used only without a mask
               "box_size_px"        : ..., # from the volume header
               "pixel_size_A_per_px": ..., # from the volume header
    }
    outputs = {"aligned_volume_filepath": ...,
               "aligned_mask_filepath"  : None, # only when --mask
               "center_zyx_px"          : ...,  # particle center, the rotation pivot
               "rotation_zyx"           : ...,  # matrix passed to affine_transform; columns: shortest, middle, longest axis
               "principal_variances_px2": ...,  # shortest, middle, longest
               "skewness"               : ...,  # along the oriented axes
               "figure_filepath"        : None, # only when --save
    }

    ### 3. PREPROCESSING ###
    logger.info("Loading volume...")
    volume_mrc = utils.mrc.load(inputs["volume_filepath"])
    volume     = volume_mrc["data"]
    inputs["box_size_px"]         = volume.shape[0]
    inputs["pixel_size_A_per_px"] = volume_mrc["voxel_size_A_per_px"][0]
    
    mask = None
    if inputs["mask_filepath"]:
        logger.info("Loading mask...")
        mask = utils.mrc.load(inputs["mask_filepath"])["data"]
        logger.info(f"+ Binary Mask? {volops.is_binary(mask)}")

    ### 4. MAIN ###
    logger.info(f"Running alignment...")
    values, data = run(volume, mask, inputs["threshold"])
    outputs.update(values)

    ### 5. POSTPROCESSING ###
    # save aligned volume
    outputs["aligned_volume_filepath"] = os.path.join(args.output_path or ".", f"aligned_{Path(inputs['volume_filepath']).name}")
    utils.mrc.save(volume     = data["aligned_volume"],
                   voxel_size = volume_mrc["voxel_size_A_per_px"],
                   filename   = outputs["aligned_volume_filepath"])

    # save aligned mask
    if mask is not None:
        outputs["aligned_mask_filepath"] = os.path.join(args.output_path or ".", f"aligned_{Path(inputs['mask_filepath']).name}")
        utils.mrc.save(volume     = data["aligned_mask"],
                       voxel_size = volume_mrc["voxel_size_A_per_px"],
                       filename   = outputs["aligned_mask_filepath"])
    # save figures
    if args.save:
        logger.info("Generating figures...")
        outputs["figure_filepath"] = os.path.join(args.output_path or ".", "orthogonal_view.png")

        generate_figures(original_segmented = mask if mask is not None else volops.binary_segmentation(volume, inputs["threshold"]),
                         aligned_segmented  = data["aligned_mask"],
                         titles             = ["Original View (Max Projections)", "Aligned and Centered Volume (Max Projections)"],
                         output_path        = outputs["figure_filepath"])
        logger.info(f"+ saved to {outputs['figure_filepath']}")

    # save I/O 
    result = utils.output.print_and_save({"input":inputs, "output":outputs}, 
                                        print_as="json" if args.json else "yaml",
                                        filepath=os.path.join(args.output_path, __myname__) if args.output_path else None)
    
    # logger.info(f"Result:\n{result['yaml']}")
    logger.info(f"Exiting...")
    logger.info("-"*40)
