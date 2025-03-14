import os
import cv2
import dlib
import click
import logging
import numpy as np

from pathlib import Path
from PIL import Image, ImageFile

# Set up basic logging configuration
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Rotator:
    IMAGES_DIRECTORY = "/images"

    def __init__(self, overwrite_files: bool = False):
        self.detector = dlib.get_frontal_face_detector()
        self.overwrite_files = overwrite_files
        logger.info(f"Rotator initialized. Overwrite files: {self.overwrite_files}")

    def get_images(self):
        """Scan the images directory and return a list of image file paths using the same logic as before."""
        images = []
        for root_dir, sub_dir, files in os.walk(self.IMAGES_DIRECTORY):
            for file_name in files:
                if file_name.lower().endswith(('.jpeg', '.jpg', '.png')):
                    base_name, extension = os.path.splitext(file_name)
                    if not base_name.endswith('_b'):
                        file_path = os.path.join(root_dir, file_name)
                        images.append(file_path)
        return images

    def populate_image_list(self, list_widget):
        """Populate a given GUI list widget with image file paths."""
        images = self.get_images()
        list_widget.clear()
        list_widget.addItems(images)

    def analyze_images(self):
        """
        Recursively loop through all files and subdirectories,
        looking for images to analyze and rotate.
        """
        images = self.get_images()

        logger.info(f"Found {len(images)} image(s) in {self.IMAGES_DIRECTORY}.")
        rotations = {}
        with click.progressbar(images, label=f"Analyzing {len(images)} Images...") as filepaths:
            for filepath in filepaths:
                image = self.open_image(filepath)
                rotation = self.analyze_image(image, filepath)

                if rotation:
                    rotations[filepath] = rotation

        logger.info(f"{len(rotations)} Image(s) Rotated.")
        for filepath, rotation in rotations.items():
            logger.info(f" - {filepath} (Rotated {rotation} Degrees)")

    def analyze_image(self, image: ImageFile, filepath: str) -> int:
        """
        Cycles through 4 image rotations of 90 degrees each.
        Saves the image at the current rotation if faces are detected.
        Returns the rotation in degrees if any rotation occurred, otherwise 0.
        """
        for cycle in range(4):
            # Rotate the image if we are in a later cycle
            if cycle > 0:
                image = image.rotate(90, expand=True)
                logger.debug(f"Rotating '{filepath}' by 90 degrees (attempt #{cycle}).")

            # Convert to numpy array for face detection
            image_copy = np.asarray(image)
            image_gray = cv2.cvtColor(image_copy, cv2.COLOR_BGR2GRAY)

            faces = self.detector(image_gray, 0)
            if len(faces) == 0:
                logger.debug(f"No faces found in '{filepath}' at rotation #{cycle}.")
                continue

            # If we detect faces on a rotation > 0, save the image
            if cycle > 0:
                logger.info(f"Faces found in '{filepath}'. Rotating by {cycle * 90} degrees.")
                self.save_image(image, filepath)
                return cycle * 90

        return 0

    def open_image(self, filepath: str) -> ImageFile:
        """Open an image file using Pillow."""
        try:
            image = Image.open(filepath)
            logger.debug(f"Image '{filepath}' opened successfully.")
            return image
        except Exception as e:
            logger.error(f"Error opening image '{filepath}': {e}")
            return None

    def save_image(self, image: ImageFile, filepath: str) -> bool:
        """Save the rotated image using Pillow."""
        if not self.overwrite_files:
            # Insert '-rotated' before the first dot in the filename
            filepath = filepath.replace(".", "-rotated.", 1)
            logger.debug(f"Saving rotated image as '{filepath}'.")

        try:
            image.save(filepath)
            logger.info(f"Image saved successfully at '{filepath}'.")
            return True
        except Exception as e:
            logger.error(f"Error saving image '{filepath}': {e}")
            return False


@click.command()
@click.argument("overwrite_files", type=click.BOOL, default=False)
def cli(overwrite_files: bool = False):
    rotator = Rotator(overwrite_files)
    rotator.analyze_images()


if __name__ == "__main__":
    cli()