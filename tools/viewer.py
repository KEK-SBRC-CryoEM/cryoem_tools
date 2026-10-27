"""
 A quick and dirty "lightweight" image viewer for x11 forwarding.
    Keys: 
        1, 2, 3 adjust image size (1:original, 2 and 3: downscaled);
        Q or Esc: quit.
"""

import argparse
import logging
import os
from pathlib import Path

# mute Qt warnings (like the QFontDatabase missing fonts error) before importing cv2
os.environ.setdefault("QT_LOGGING_RULES", "*=false")
os.environ.setdefault("OPENCV_LOG_LEVEL", "ERROR")
import cv2

from spa import utils

__myname__ = Path(__file__).stem
logger = logging.getLogger(__myname__)

# quality mode (none: original)
MAX_SIZE = {1: None, 2: (1200, 900), 3: (800, 600)}

def get_resized_image(img, max_size):
    # downscale img while keeping the aspect ratio
    if max_size is None:
        return img

    height, width = img.shape[:2]
    scale = min(max_size[0] / width, max_size[1] / height)

    if scale >= 1: # no rescaling needed
        return img

    new_size = (max(1, int(width * scale)), max(1, int(height * scale)))
    return cv2.resize(img, new_size, interpolation=cv2.INTER_AREA)

def is_window_open(name):
    try:
        return cv2.getWindowProperty(name, cv2.WND_PROP_VISIBLE) >= 1
    except cv2.error:
        return False

def update_display(img, mode, window_name, title):
    # resize
    img_resized = get_resized_image(img, MAX_SIZE[mode])
    
    # change the window size
    h, w = img_resized.shape[:2]
    cv2.setWindowTitle(window_name, f"{title}  [{w}x{h}, quality {mode}]  1/2/3: size  Q: quit")
    cv2.resizeWindow(window_name, w, h)

    # display
    cv2.imshow(window_name, img_resized)

def view(img, title, mode=1):
    # create window
    window_name  = "cspa-view"
    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)

    # resize and update display
    update_display(img, mode, window_name, title)

    # key listening
    try:
        while True:
            key = cv2.waitKey(50) & 0xFF # wait 50ms, return -1 if not key is pressed
            # ESC, Q or closing the window to quit
            if key in (27, ord("q"), ord("Q")) or not is_window_open(window_name):
                break
            if key in (ord("1"), ord("2"), ord("3")) and key - ord("0") != mode:
                mode = key - ord("0")
                update_display(img, mode, window_name, title)
    except KeyboardInterrupt:
        pass

    cv2.destroyAllWindows()

if __name__ == "__main__":
    ########## CLI setup ##########
    parser = argparse.ArgumentParser(description="Lightweight image viewer for X11 forwarding.")
    parser.add_argument("image_path", help="image file (PNG, JPEG, TIFF, ...)")
    parser.add_argument("-q", "--quality", type=int, choices=MAX_SIZE, default=3, help="1 (original), 2 (medium), 3 (low quality, faster)")
    parser.add_argument("--verbose", action="store_true", help="Enable more detailed logging.")

    args = parser.parse_args()
    utils.log.configure_logging(verbose=args.verbose)
    ##### / #####

    img = cv2.imread(args.image_path)
    if img is None:
        logger.error(f"could not read '{args.image_path}' (missing file or unsupported format)")
    else:
        view(img, title=os.path.basename(args.image_path), mode=args.quality)
