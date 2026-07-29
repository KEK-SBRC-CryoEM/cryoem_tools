import mrcfile

## mrc file related ##
def load(filename):
    data = {}
    with mrcfile.open(filename) as mrc:
        data["data"]                = mrc.data
        data["voxel_size_A_per_px"] = mrc.voxel_size.tolist() # Å/pixel
        data["shape"]               = mrc.data.shape          # size of the box
    return data

def save(volume, voxel_size, filename):
    with mrcfile.new(filename, overwrite=True) as mrc:
        mrc.set_data(volume)
        mrc.voxel_size = voxel_size