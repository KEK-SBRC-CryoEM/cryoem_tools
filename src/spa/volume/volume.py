import numpy as np

from scipy import stats
from scipy.ndimage import affine_transform

from miniball import miniball

## projections ##
def get_max_projection(volume):
    return [volume.max(axis=i) for i in [0,1,2]]

def get_summed_projection(volume):
    return [volume.sum(axis=i) for i in [0,1,2]]

def get_mean_projection(volume):
    return [volume.mean(axis=i) for i in [0,1,2]]

def get_orthogonal_slices(volume, center=None):
    if center is None:
        cz, cy, cx = volume.shape[0]//2, volume.shape[1]//2, volume.shape[2]//2
    else:
        cz, cy, cx = center
    return [volume[cz, :, :], volume[:, cy, :], volume[:, :, cx]]

## standardization and segmentation ## 
def standardize(volume):
    mean = np.mean(volume)
    std = np.std(volume, ddof=0) + 1e-12
    return (volume - mean) / std

def binary_segmentation(data, threshold=0, is_binary_mask=False):
    """
    Perform binary segmentation on a 3D volume by thresholding.

    Parameters:
        data (np.ndarray): 3D numpy array representing the density map or volume.
        threshold (float): Threshold value for segmentation. Voxels with 
                                     values greater than this threshold are considered foreground. 
        is_binary_mask (bool, optional, default=False): If False, sets voxels outside a centered 
                                            spherical region (corners) to 0. 
                                            If True, interprets the volume as a binary mask and 
                                            applies only simple thresholding (faster).
    Returns:
        np.ndarray: An int8 array (same shape as input) where 1 indicates voxels 
                    above the threshold (segmented region), and 0 otherwise.
    """
    segmented = np.zeros_like(data, dtype=np.int8)
    segmented[data > threshold]  = +1
    segmented[data <= threshold] = 0

    # set 0 to voxels outside sphere bounds
    if not is_binary_mask:
        radius = np.max(data.shape)//2
        z_dim, y_dim, x_dim = data.shape
        center_z, center_y, center_x = z_dim // 2, y_dim // 2, x_dim // 2
    
        z, y, x = np.meshgrid(np.arange(z_dim), np.arange(y_dim), np.arange(x_dim), indexing='ij')
        distances = np.sqrt((x - center_x)**2 + (y - center_y)**2 + (z - center_z)**2)
    
        mask = (distances > radius)
        segmented[mask] = 0
    
    return segmented

def is_binary(mask):
    return np.all((mask == 0) | (mask == 1))

## image processing ##
def get_spherical_kernel(size):
    z, y, x = np.ogrid[-size//2 : size//2, -size//2 : size//2, -size//2 : size//2]
    return x**2 + y**2 + z**2 <= (size/2)**2

## miniball enclosing sphere ##
def compute_enclosing_sphere(coordinates):
    """
    Computes the smallest sphere enclosing the given coordinates.

    Parameters:
        coordinates (np.ndarray): (N, 3) array of voxel coordinates of the segmented region,
            e.g. from get_coordinates(binary_mask).

    Returns:
        dict: Sphere from the miniball algorithm, with "diameter" added:
            "center"   (np.ndarray, shape (3,)): sphere center
            "radius"   (float): radius
            "diameter" (float): 2 * radius

    Raises:
        ValueError: if coordinates is empty.
    """
    if coordinates.size == 0:
        raise ValueError("compute_enclosing_sphere: no coordinates given (empty segmentation?).")
    result = miniball(coordinates)
    result["diameter"] = 2 * result["radius"]
    return result

## mask ##
def create_spherical_mask(shape, radius, center=None):
    """
    Create a 3D spherical mask with binary values (1 inside sphere, 0 outside).
    
    Parameters:
        shape (tuple): shape of the volume, e.g. (256, 256, 256)
        radius (float): radius of the sphere in voxels
        center (tuple or None): (z, y, x) center of the sphere. If None, uses center of volume
        filename (str): output .mrc file 
    """
    Z, Y, X = np.indices(shape)

    if center is None:
        center = np.array(shape) / 2

    dist = np.sqrt((X - center[2])**2 + (Y - center[1])**2 + (Z - center[0])**2)
    mask = (dist <= radius).astype(np.uint8)
    
    return mask

## alignment ##
def get_coordinates(volume_segmented) -> np.ndarray:
    """(N, 3) voxel coordinates of a mask or segmented volume"""
    return np.column_stack(np.where(volume_segmented == 1)).astype(np.float64)

def get_center(coordinates, mode="coordinates") -> np.ndarray:
    """Define the rotation pivot
        - "coordinates" = coordinate mean
        - "sphere"      = enclosing-sphere center.
    """
    if mode == "coordinates":
        return coordinates.mean(axis=0)
    elif mode == "sphere":
        return compute_enclosing_sphere(coordinates)["center"]
    raise ValueError(f"get_center: unknown mode {mode}; expected 'coordinates' or 'sphere'")

def apply_transform(volume, R, pivot, order:int=0) -> np.ndarray:
    """ Apply affine transform on volume for matrix R and pivot with interpolation defined by 'order'."""
    box_center = (np.array(volume.shape) - 1) / 2.0
    offset = pivot - R @ box_center

    rotate_volume = affine_transform(volume, R, 
                                     offset = offset, 
                                     order  = order, 
                                     mode   = "constant", 
                                     cval   = 0.0)
    
    return rotate_volume

def compute_axes_directions(coordinates, axes):
    """
    Resolve the sign ambiguity of PCA principal axes using distribution skewness and enforcing det>0.

    Each eigenvector has a sign ambiguity that makes it not possible to distinguish 180° rotations (e.g.: top-down and bottom-up are equivalent), and an arbitrary combination of signs can result in mirroring.

    This function orient the two axes with the largest absolute skewness toward the longer tail (positive skewness). The remaining axis is oriented so that the frame is right-handed, i.e. ``det(axes) = +1``.

    Parameters:
        coordinates (np.ndarray): (N, 3) voxel coordinates
        axes (np.ndarray): (3, 3) principal axes (shortest, middle, longest).
            - ``axes[:, 0]`` — shortest principal axis
            - ``axes[:, 1]`` — middle principal axis
            - ``axes[:, 2]`` — longest principal axis

    Returns:
        np.ndarray: (3, 3) axes with chosen directions.
        np.ndarray: (3,) skewness projections along each axis
    """
    # sign order by skewness
    gamma = stats.skew(coordinates @ axes, axis=0)
    order = np.argsort(-np.abs(gamma))             # most skewed to least
    signs = np.where(gamma < 0, -1.0, 1.0)         # point each axis toward its longer tail

    # enforce signs and determinant>0
    determinant = np.linalg.det(axes)
    signs[order[2]] = signs[order[0]] * signs[order[1]] * np.sign(determinant)   # least skewed: det = +1
    return axes * signs, gamma * signs

def compute_principal_axes(coordinates) -> np.ndarray:
    """
    Principal axes of the coordinates, as the matrix for affine_transform.

    Parameters:
        coordinates (np.ndarray): (N, 3) voxel coordinates, array order (z, y, x).

    Returns:
        np.ndarray: (3, 3) matrix 
    """
    cov = np.cov(coordinates, rowvar=False)
    eigvals, eigvecs = np.linalg.eigh(cov) # ascending: columns = shortest, middle, longest 
    return eigvals, eigvecs

def covariance_alignment(volume, binary_mask, center_mode="coordinates", order=3):
    coords = get_coordinates(binary_mask)
    pivot  = get_center(coords, center_mode)
    # find longest, middle, shortest view
    eigvals, eigvecs = compute_principal_axes(coords) 
    # find the direction of each view 
    axes, skewness   = compute_axes_directions(coords, eigvecs) # PCA sign ambiguities: 180 rotation and mirroring

    R = axes
    result = {"volume"  : apply_transform(volume,      R, pivot, order=order) if volume is not None else None,
              "mask"    : apply_transform(binary_mask, R, pivot, order=0),
              "eigvals" : eigvals,
              "eigvecs" : eigvecs,
              "skewness": skewness,
              "offset"  : pivot,
    }

    return result


