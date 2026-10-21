"""Volume-domain operations."""
# Note: as this grows, 
#       it may be worth splitting volume.py into additional files
#       eg: projection, segmentation, sphere, alignment

from .volume import (
    get_max_projection,
    get_summed_projection,
    get_mean_projection,
    get_orthogonal_slices,
    standardize,
    binary_segmentation,
    is_binary,
    compute_enclosing_sphere,
    create_spherical_mask,
    get_spherical_kernel,
    # alignment
    get_coordinates,
    get_center,
    apply_transform,
    compute_principal_axes,
    compute_axes_directions,
    covariance_alignment,
)

__all__ = [
    "get_max_projection",
    "get_summed_projection",
    "get_mean_projection",
    "get_orthogonal_slices",
    "standardize",
    "binary_segmentation",
    "is_binary",
    "compute_enclosing_sphere",
    "create_spherical_mask",
    "get_spherical_kernel",
    # alignment
    "get_coordinates",
    "get_center",
    "apply_transform",
    "compute_principal_axes",
    "compute_axes_directions",
    "covariance_alignment",
]