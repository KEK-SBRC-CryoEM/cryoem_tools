import numpy as np

FFT_FRIENDLY_SIZES = np.array([24, 32, 36, 40, 44, 48, 52, 56, 60, 64,
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
],dtype=np.int32,)
FFT_FRIENDLY_SIZES.flags.writeable = False


def adjust_box(box:int|float, scaling:float=1, fft_friendly:bool=False, make_even:bool=False):
    """Apply box-size adjustments in the following order:
        1. Scale the box size by ``scaling``.
        2. Round up to an FFT-friendly value if ``fft_friendly`` is True.
        3. Round up to an even integer if ``make_even`` is True.
    """

    # 1. scale
    box = box*scaling

    # 2. FFT-friendly
    if fft_friendly:
        box = round_up_to_eman2(box)
    
    # 3. even 
    if make_even:
        box = round_up_to_even(box)

    return box

def round_up_to_even(box:int|float) -> int:
    """Round a number up to the nearest even integer value."""
    return int(2*np.ceil(box/2))

### general
def round_up_to_eman2(box:int|float) -> int:
    """
    Round a number up to the nearest value in the EMAN2 FFT-friendly list.
    The complete list is available at: https://blake.bcm.edu/emanwiki/EMAN2/BoxSize
    """
    result = box

    mask = (result <= FFT_FRIENDLY_SIZES)
    if sum(mask) > 0:
        result = FFT_FRIENDLY_SIZES[mask].min()
    
    return result