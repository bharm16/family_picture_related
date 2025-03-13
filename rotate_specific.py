import os
import cv2
import dlib
import click
import logging
import numpy as np

from pathlib import Path
from PIL import Image, ImageFile

# Set up detailed logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)

class Rotator:
    # 1. Update this path to your directory
    IMAGES_DIRECTORY = (
        "/Users/bryceharmon/Library/CloudStorage/GoogleDrive-bharm257@gmail.com/"
        "My Drive/Family_Photos_25_Scans copy/photos_ending_in_a"
    )

    def __init__(self, overwrite_files: bool = False):
        self.detector = dlib.get_frontal_face_detector()
        self.overwrite_files = overwrite_files
        logger.info(f"Rotator initialized. Overwrite files: {self.overwrite_files}")

    def analyze_images(self):
        """
        Recursively loop through all files and subdirectories in IMAGES_DIRECTORY,
        collecting only images beginning with 'all_other_photos' and not ending in '_b'.
        Then rotate those containing faces.
        """
        images = []
        logger.debug(f"Starting to walk through: {self.IMAGES_DIRECTORY}")

        for root_dir, sub_dir, files in os.walk(self.IMAGES_DIRECTORY):
            logger.debug(f"Inspecting directory: {root_dir}")
            for file_name in files:
                # Make sure extension is right, name starts with 'all_other_photos' but not ending with '_b'
                if file_name.lower().endswith((".jpeg", ".jpg", ".png")):
                    base_name, extension = os.path.splitext(file_name)
                    if base_name.startswith("all_other_photos") and not base_name.endswith("_b"):
                        file_path = str(os.path.join(root_dir, file_name))
                        images.append(file_path)
                        logger.debug(f"Queued image for analysis: {file_path}")
                    else:
                        logger.debug(f"Skipping file: {file_name}")

        logger.info(f"Found {len(images)} eligible image(s) in {self.IMAGES_DIRECTORY}.")
        rotations = {}

        with click.progressbar(images, label=f"Analyzing {len(images)} Images...") as filepaths:
            for filepath in filepaths:
                image = self.open_image(filepath)
                if image:
                    rotation = self.analyze_image(image, filepath)
                    if rotation:
                        rotations[filepath] = rotation

        logger.info(f"{len(rotations)} Image(s) Rotated.")
        for filepath, rotation in rotations.items():
            logger.info(f" - {filepath} (Rotated {rotation} Degrees)")

    def analyze_image(self, image: ImageFile, filepath: str) -> int:
        """
        Attempt up to 4 rotations (0°, 90°, 180°, 270°) until
        a face is detected. If found at a non-zero rotation,
        overwrite (or create a rotated copy) and return the degrees rotated.
        """
        logger.debug(f"Analyzing image: {filepath}")
        for cycle in range(4):
            # Rotate if we are in a later cycle
            if cycle > 0:
                image = image.rotate(90, expand=True)
                logger.debug(f"Rotating '{filepath}' by 90 degrees (attempt #{cycle}).")

            # Convert to numpy array for face detection
            image_copy = np.asarray(image)
            image_gray = cv2.cvtColor(image_copy, cv2.COLOR_BGR2GRAY)
            logger.debug(f"Performing face detection on '{filepath}', rotation cycle {cycle}")

            faces = self.detector(image_gray, 0)
            logger.debug(f"Found {len(faces)} face(s) in '{filepath}' at rotation cycle {cycle}.")

            if len(faces) == 0:
                continue

            # If we detect faces at a non-zero rotation, save the image
            if cycle > 0:
                degrees = cycle * 90
                logger.info(f"Faces detected in '{filepath}'. Rotating by {degrees} degrees.")
                self.save_image(image, filepath)
                return degrees

        return 0

    def open_image(self, filepath: str) -> ImageFile:
        """Open an image file using Pillow."""
        logger.debug(f"Opening image: {filepath}")
        try:
            image = Image.open(filepath)
            logger.debug(f"Image '{filepath}' opened successfully.")
            return image
        except Exception as e:
            logger.error(f"Error opening image '{filepath}': {e}")
            return None

    def save_image(self, image: ImageFile, filepath: str) -> bool:
        """Overwrite or save a rotated copy using Pillow."""
        if not self.overwrite_files:
            # Insert '-rotated' before the first dot in the filename if not overwriting
            rotated_path = filepath.replace(".", "-rotated.", 1)
            logger.debug(f"Saving rotated image as '{rotated_path}'.")
        else:
            # Overwrite existing file
            rotated_path = filepath
            logger.debug(f"Overwriting original file: '{rotated_path}'.")

        try:
            image.save(rotated_path)
            logger.info(f"Image saved successfully at '{rotated_path}'.")
            return True
        except Exception as e:
            logger.error(f"Error saving image '{rotated_path}': {e}")
            return False


@click.command()
@click.argument("overwrite_files", type=click.BOOL, default=False)
def cli(overwrite_files: bool = False):
    rotator = Rotator(overwrite_files)
    rotator.analyze_images()


if __name__ == "__main__":
    # Run with `python rotate.py True` for overwriting
    cli()