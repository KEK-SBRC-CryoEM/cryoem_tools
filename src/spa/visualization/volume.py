import numpy as np
import cv2 as cv
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

## opencv related ##
def normalize_to_uint8(img, max_value):
    return (255*img/max_value).astype(np.uint8)

def binary_to_grayscale(img):
    img_gray = img.astype(np.uint8) * 255
    return img_gray

def show_slices(imgs_gray, spheres=None, title="", output_path=None):
    plt.close('all')
    subtitles = ["XY", "XZ", "YZ"]
    indices = [(2,1), (2,0), (1,0)]

    # convert to rgb to enable drawing colored circles
    imgs_rgb = [cv.cvtColor(img, cv.COLOR_GRAY2RGB) for img in imgs_gray]

    # draw circles on each projected image
    for j, sphere in enumerate(spheres or []):
        r = int(np.ceil(sphere["radius"]))
        for i in range(3):
            overlay = imgs_rgb[i].copy()
            ax = int(np.ceil(sphere["center"][indices[i][0]]))
            ay = int(np.ceil(sphere["center"][indices[i][1]]))
            cv.circle(overlay, (ax, ay), r, sphere["plot"]["color"], 2)
            imgs_rgb[i] = cv.addWeighted(overlay, sphere["plot"]["alpha"], imgs_rgb[i], 1-sphere["plot"]["alpha"], 0)

    # plot images
    fig, axs = plt.subplots(1, 3, figsize=(12, 4))
    for i in range(3):
        axs[i].imshow(imgs_rgb[i])
        axs[i].set_title(subtitles[i])

    # colorbar
    sm = plt.cm.ScalarMappable(cmap='gray', norm=plt.Normalize(vmin=0, vmax=255))
    fig.colorbar(sm, ax=axs, orientation='vertical', fraction=0.02, pad=0.04)

    fig.suptitle(title, fontsize=14)
    if output_path:
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
    else:
        plt.show()