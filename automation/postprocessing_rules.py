## temporary script for testing; need refactoring ##

import numpy as np
from pathlib import Path

# logger = logging.getLogger("Postprocessing rules")

### micrograph related
def compute_extract_coordinates_min(boxsize, lower_bound=0):
    return int(lower_bound + (boxsize // 2))

def compute_extract_coordinates_max(boxsize, upper_bound):
    return int(upper_bound - (boxsize // 2))

### map size related
def padding(particle_diameter, pixel_size, padding_pixels=0, padding_angstrom=0, padding_percentage=0):
    # voxels
    result  = particle_diameter
    result += padding_pixels

    # convert to angstrom
    result *= pixel_size
    result += padding_angstrom

    # percentage padding
    result *= (1.0+padding_percentage)

    return int(np.ceil(result))

def compute_size_in_real_space(particle_diameter, pixel_size):
    return particle_diameter * pixel_size

def compute_binned_box_size(boxsize, binning_factor):
    return boxsize / binning_factor

### boxsize related
def choose_ctfbox_or_negbox(box_size_1, pixel_size_1, binning_factor_1, 
                             box_size_2, pixel_size_2, binning_factor_2):
    # convert to angstrom
    diameter_1 = box_size_1 * pixel_size_1
    diameter_2 = box_size_2 * pixel_size_2

    # get the biggest in pixel (comparison in angstrom)
    if diameter_1 >= diameter_2:
        result = adjust_boxsize(box_size_1*binning_factor_1, even=True)
    else:
        result = (box_size_2*binning_factor_2) / 0.95

    return result

def adjust_boxsize(box, scaling=1, use_eman_boxsizes=False, even=False):
    # scaling = 1/binning_factor
    box = box*scaling
    if use_eman_boxsizes:
        box = get_next_eman_boxsize(box)
    if even:
        box = int(2*np.ceil(box/2))
    return box

def get_next_eman_boxsize(n):
    """
    Return the smallest element in the list that is ≥ than the input boxsize
    """
    boxsize_list = np.array([24, 32, 36, 40, 44, 48, 52, 56, 60, 64,
                                72, 84, 96, 100, 104, 112, 120, 128, 132, 140,
                                168, 180, 192, 196, 208, 216, 220, 224, 240, 256,
                                260, 288, 300, 320, 352, 360, 384, 416, 440, 448,
                                480, 512, 540, 560, 576, 588, 600, 630, 640, 648,
                                672, 686, 700, 720, 750, 756, 768, 784, 800, 810,
                                840, 864, 882, 896, 900, 960, 972, 980, 1000, 1008, 
                                1024, 
                                # values below are not empirically tested
                                1050, 1080, 1120, 1134, 1152, 1176, 1200, 1250, 1260,
                                1280, 1296, 1344, 1350, 1372, 1400, 1440, 1458, 1470,
                                1500, 1512, 1536, 1568, 1600, 1620, 1680, 1728, 1750,
                                1764, 1792, 1800, 1890, 1920, 1944, 1960, 2000, 2016,
                                2048, 2058, 2100, 2160, 2240, 2250, 2268, 2304, 2352,
                                2400, 2430, 2450, 2500, 2520, 2560, 2592, 2646, 2688,
                                2700, 2744, 2800, 2880, 2916, 2940, 3000, 3024, 3072,
                                3136, 3150, 3200, 3240, 3360, 3402, 3430, 3456, 3500,
                                3528, 3584, 3600, 3750, 3780, 3840, 3888, 3920, 4000,
                                4032, 4050, 4096 
    ]) # from: https://blake.bcm.edu/emanwiki/EMAN2/BoxSize
    

    result = n

    mask = (result <= boxsize_list)
    if sum(mask) > 0:
        result = boxsize_list[mask].min()
    
    return result

### data structure related
def get_pixel_size(voxel_size):
    return voxel_size[0] if isinstance(voxel_size, list) else voxel_size

### file / directory 
def get_filename_from_path(path):
    return Path(path).name