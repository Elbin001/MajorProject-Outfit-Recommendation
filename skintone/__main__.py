import functools
import logging
import os
import shutil
import glob
import sys
import threading
from datetime import datetime
from multiprocessing import freeze_support, cpu_count, Pool
from typing import List

import cv2
import numpy as np
from tqdm import tqdm
from tqdm.contrib.logging import logging_redirect_tqdm

from stone.api import process
from stone.package import (
    __app_name__,
    __version__,
    __description__,
    __copyright__,
    __url__,
    __author__,
    __license__,
    __code__,
    __issues__,
    __package_name__,
)
from stone.utils import (
    build_arguments,
    build_image_paths,
    is_windows,
    ArgumentError,
    is_debugging,
    resolve_labels,
)

LOG = logging.getLogger(__name__)
lock = threading.Lock()

use_cli = len(sys.argv) > 1 and "--gui" not in sys.argv


def process_in_main(
    filename_or_url,
    image_type,
    tone_palette,
    tone_labels,
    convert_to_black_white,
    n_dominant_colors=2,
    new_width=250,
    scale=1.1,
    min_nbrs=5,
    min_size=(90, 90),
    threshold=0.3,
    return_report_image=False,
):
    """
    This is a wrapper function that calls process() in the main process to avoid pickling error.
    :param filename_or_url:
    :param image_type:
    :param tone_palette:
    :param tone_labels:
    :param convert_to_black_white:
    :param n_dominant_colors:
    :param new_width:
    :param scale:
    :param min_nbrs:
    :param min_size:
    :param threshold:
    :param return_report_image:
    :return:
    """
    try:
        return process(
            filename_or_url,
            image_type=image_type,
            tone_palette=tone_palette,
            tone_labels=tone_labels,
            convert_to_black_white=convert_to_black_white,
            n_dominant_colors=n_dominant_colors,
            new_width=new_width,
            scale=scale,
            min_nbrs=min_nbrs,
            min_size=min_size,
            threshold=threshold,
            return_report_image=return_report_image,
        )
    except ArgumentError as e:
        # Abort the app if any argument error occurs
        raise e
    except Exception as e:
        msg = f"Error processing image {filename_or_url}: {str(e)}"
        LOG.error(msg)
        return {
            "filename": filename_or_url,
            "message": msg,
        }


def main():
    # Hardcoded input and output paths
    input_dir = r"D:\MajorProject-Outfit-Recommendation\uploads"  # Replace with your input image path
    output_dir = r"D:\MajorProject-Outfit-Recommendation\output"  # Replace with your desired output directory
    os.makedirs(output_dir, exist_ok=True)

    # Setup logger
    now = datetime.now()
    log_dir = os.path.join(output_dir, "./log")
    os.makedirs(log_dir, exist_ok=True)

    logging.basicConfig(
        filename=now.strftime(f"{log_dir}/log-%y%m%d%H%M.log"),
        level=logging.INFO,
        format="[%(asctime)s] {%(filename)s:%(lineno)4d} %(levelname)s - %(message)s",
        datefmt="%H:%M:%S",
    )

        # Get all valid image files in the input directory
    valid_extensions = ["*.jpg", "*.jpeg", "*.png", "*.webp", "*.gif", "*.tif"]
    image_paths = []
    for ext in valid_extensions:
        image_paths.extend(glob.glob(os.path.join(input_dir, ext)))

    if not image_paths:
        print(f"No valid images found in directory: {input_dir}")
        return
    # Set fixed parameters
    #image_paths = [input_image_path]  # Single hardcoded image path
    image_type_setting = "color"  # Restrict to color images
    specified_palette = "perla"  # Default palette
    specified_tone_labels = None  # Use default labels
    new_width = 250
    n_dominant_colors = 2
    min_size = (90, 90)
    scale = 1.1
    min_nbrs = 5
    threshold = 0.15

    print(f"Processing {len(image_paths)} image(s) in directory: {input_dir}")
    
    for image_path in image_paths:
        try:
            # Process the image
            result = process(
                filename_or_url=image_path,
                image_type=image_type_setting,
                tone_palette=specified_palette,
                tone_labels=specified_tone_labels,
                convert_to_black_white=False,
                n_dominant_colors=n_dominant_colors,
                new_width=new_width,
                scale=scale,
                min_nbrs=min_nbrs,
                min_size=min_size,
                threshold=threshold,
                return_report_image=False,
            )

            # Print results to the terminal
            if result and "faces" in result:
                for face in result["faces"]:
                    seasonal_tone = get_seasonal_tone(face["skin_tone"])
                    #print(f"\nFace ID: {face['face_id']}")
                    #print(f"  Dominant Colors: {face['dominant_colors']}")
                    #print(f"  Skin Tone: {face['skin_tone']}")
                    print(f"Seasonal Tone: {seasonal_tone}")
                    #print(f"  Accuracy: {face['accuracy']}%")
            else:
                print("No faces detected or unable to process the image.")

        except Exception as e:
            print(f"An error occurred while processing {image_path}: {e}")
def get_seasonal_tone(hex_code):
    match hex_code.upper():
        case "#373028":
            return "Deep Autumn(rich, earthy dark tone)"
        case "#422811":
            return "Deep Autumn(warm, deep brown shade)"
        case "#513B2E":
            return "Soft Autumn(muted, warm, medium brown)"
        case "#6F503C":
            return "Warm Autumn(golden undertones in brown)"
        case "#81654F":
            return "Soft Autumn(soft and warm beige)"
        case "#9D7A54":
            return "Warm Spring(golden and warm)"
        case "#BEA07E":
            return "Warm Spring(light and warm beige)"
        case "#E5C8A6":
            return "Light Spring(peachy and warm tones)"
        case "#E7C1B8":
            return "Light Summer(soft pink undertones)"
        case "#F3DAD6":
            return "Cool Summer(light and cool pink-beige)"
        case "#FBF2F3":
            return "Light Summer(bright, cool, and soft ivory)"
        case _:
            return "Unknown Tone"



sys.argv.remove("--gui") if "--gui" in sys.argv else None
if not use_cli and "--ignore-gooey" not in sys.argv:
    try:
        from gooey import Gooey
    except ImportError:
        # If gooey is not installed, use a dummy decorator
        from stone.utils import Gooey
        from colorama import just_fix_windows_console, Fore

        just_fix_windows_console()
        print(
            Fore.YELLOW + f"You are using a CLI version of {__package_name__}.\n"
                          f"Please install the GUI version with the following command:\n",
            Fore.GREEN + f"pip install {__package_name__}[all] --upgrade\n" + Fore.RESET,
        )
        sys.exit(0)

    from importlib.resources import files

    main = Gooey(
        show_preview_warning=False,
        advanced=True,  # fixme: `False` is not working
        dump_build_config=False,  # fixme: `True` is not working, as the path cannot be resolved correctly
        target="stone",
        suppress_gooey_flag=True,
        program_name=f"{__app_name__} v{__version__}",
        required_cols=1,
        optional_cols=1,
        image_dir=str(files("stone.ui")),
        tabbed_groups=True,
        navigation="Tabbed",
        richtext_controls=True,
        use_cmd_args=True,
        menu=[
            {
                "name": "Help",
                "items": [
                    {
                        "type": "AboutDialog",
                        "menuTitle": "About",
                        "name": __app_name__,
                        "description": __description__,
                        "version": __version__,
                        "copyright": __copyright__,
                        "website": __url__,
                        "developer": __author__,
                        "license": __license__,
                    },
                    {"type": "Link", "menuTitle": "Documentation", "url": __code__},
                    {"type": "Link", "menuTitle": "Report Bugs", "url": __issues__},
                ],
            },
        ],
    )(main)

if __name__ == "__main__":
    if is_windows():
        freeze_support()
    main()
