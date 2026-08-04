import numpy as np
from spa.box import FFT_FRIENDLY_SIZES

def compute_boxes(target_rescaled_box:int|float, binning_factor:float=1.0, boxsize_list=None) -> dict|None:
    """
    Compute extraction and rescaled box sizes compatible with the target size.

    The function selects an extraction box size from a list of valid box sizes
    and computes the corresponding rescaled box size using the binning factor.
    If `boxsize_list` is not provided, a default FFT-friendly box-size list is used.

    Returns
    -------
    dict | None
        Dictionary containing:
        - `extract_box`: selected extraction box size
        - `rescaled_box`: corresponding rescaled box size

        Returns None if no compatible box size is found.
    """

    if boxsize_list is None:
        boxsize_list = FFT_FRIENDLY_SIZES

    filtered_boxes = boxsize_list[(boxsize_list>=target_rescaled_box)]
    i = np.argwhere((filtered_boxes * binning_factor) % 2 == 0)
    
    rescaled_box = extract_box = None
    if i.size>0: 
        rescaled_box = int(np.min(filtered_boxes[i]))
        extract_box  = int(rescaled_box*binning_factor)

    
    return {"extract_box" : extract_box,
            "rescaled_box": rescaled_box,}

def compute_coordinates(box:int, upper_bound_x:int  , upper_bound_y:int, 
                                 lower_bound_x:int=0, lower_bound_y:int=0) -> dict:
    """
    Compute the extraction coodinates boundaries based on the extraction box size.
    """
    return {"min_x": compute_coordinates_min(box, lower_bound_x),
            "min_y": compute_coordinates_min(box, lower_bound_y),
            "max_x": compute_coordinates_max(box, upper_bound_x),
            "max_y": compute_coordinates_max(box, upper_bound_y),
    }

def compute_coordinates_min(box:int, lower_bound:int=0) -> int:
    return int(lower_bound + (box // 2))

def compute_coordinates_max(box:int, upper_bound:int) -> int:
    return int(upper_bound - (box // 2))

