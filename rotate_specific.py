import sys
import os
import logging
import cv2
import dlib
import numpy as np

from PIL import Image, ImageFile
from PyQt5 import QtWidgets, QtGui, QtCore
import click

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ApprovalWindow(QtWidgets.QWidget):
    """
    A PyQt widget that queues image rotation proposals and displays them one at a time for user approval.
    """
    def __init__(self, rotator):
        super().__init__()
        self.rotator = rotator
        self.setWindowTitle("Image Approval")
        self.resize(1200, 800)

        self.queue = []
        self.current_item = None

        main_layout = QtWidgets.QVBoxLayout(self)
        self.item_container = QtWidgets.QWidget()
        self.item_layout = QtWidgets.QVBoxLayout(self.item_container)
        main_layout.addWidget(self.item_container)

    def queue_item(self, original_image, rotated_image, filepath, degrees):
        """Add a new image rotation proposal to the queue and display it if none is active."""
        logger.info(f"Queueing image for approval: {filepath}, proposed rotation: {degrees}°")
        self.queue.append((original_image, rotated_image, filepath, degrees))
        if self.current_item is None:
            self.show_next_item()

    def show_next_item(self):
        """Display the next item in the queue, if available."""
        logger.info(f"Showing next item. Queue length: {len(self.queue)}")
        if self.current_item:
            logger.info("Removing current item from UI.")
            self.current_item.deleteLater()
            self.current_item = None

        if self.queue:
            item = self.queue.pop(0)
            logger.info(f"Displaying new item: {item[2]}")
            self.display_item(*item)
        else:
            logger.info("No more items in queue.")
            # Optionally, clear the container or show a message indicating no pending items.
            for i in reversed(range(self.item_layout.count())):
                widget_to_remove = self.item_layout.itemAt(i).widget()
                if widget_to_remove:
                    widget_to_remove.setParent(None)

    def display_item(self, original_image, rotated_image, filepath, degrees):
        """Create and display a widget for the current image rotation proposal."""
        logger.info(f"Displaying image: {filepath}, Proposed rotation: {degrees}°")
        self.current_item = QtWidgets.QWidget()
        v_layout = QtWidgets.QVBoxLayout(self.current_item)

        # Create a horizontal layout for the images and info
        images_layout = QtWidgets.QHBoxLayout()
        orig_label = QtWidgets.QLabel()
        rotated_label = QtWidgets.QLabel()

        orig_pixmap = self.pil2pixmap(original_image)
        rotated_pixmap = self.pil2pixmap(rotated_image)

        orig_label.setPixmap(orig_pixmap)
        rotated_label.setPixmap(rotated_pixmap)
        images_layout.addWidget(orig_label)
        images_layout.addWidget(rotated_label)

        info_label = QtWidgets.QLabel(f"File: {filepath}\nProposed rotation: {degrees}°")
        images_layout.addWidget(info_label)

        v_layout.addLayout(images_layout)

        # Create a horizontal layout for the approve and reject buttons below the images
        buttons_layout = QtWidgets.QHBoxLayout()
        approve_button = QtWidgets.QPushButton("Approve")
        reject_button = QtWidgets.QPushButton("Reject")
        buttons_layout.addWidget(approve_button)
        buttons_layout.addWidget(reject_button)

        v_layout.addLayout(buttons_layout)

        approve_button.clicked.connect(lambda: self.on_approve(filepath, rotated_image))
        reject_button.clicked.connect(self.on_reject)

        # Clear previous content and add the new item widget
        for i in reversed(range(self.item_layout.count())):
            widget_to_remove = self.item_layout.itemAt(i).widget()
            if widget_to_remove:
                widget_to_remove.setParent(None)
        self.item_layout.addWidget(self.current_item)

    def on_approve(self, filepath, rotated_image):
        """Approve the rotation: save the rotated image and show the next queued item."""
        logger.info(f"Image approved: {filepath}, saving rotated image.")
        self.rotator.save_image(rotated_image, filepath)
        self.show_next_item()

    def on_reject(self):
        """Reject the rotation proposal and show the next queued item."""
        logger.info("Image rotation rejected.")
        self.show_next_item()

    def pil2pixmap(self, pil_image):
        """Convert a Pillow Image into a QPixmap for display."""
        try:
            if pil_image.mode != "RGB":
                pil_image = pil_image.convert("RGB")
            display_img = pil_image.copy()
            display_img.thumbnail((400, 400))
            data = display_img.tobytes("raw", "RGB")
            bytes_per_line = display_img.width * 3
            qimage = QtGui.QImage(
                data,
                display_img.width,
                display_img.height,
                bytes_per_line,
                QtGui.QImage.Format_RGB888,
            )
            pixmap = QtGui.QPixmap.fromImage(qimage)
            logger.info("Successfully converted PIL image to QPixmap.")
            return pixmap
        except Exception as e:
            logger.error(f"Error converting image to QPixmap: {e}")
            return QtGui.QPixmap()

class Rotator:
    # Point this to the directory with your images:
    IMAGES_DIRECTORY = '/Users/bryceharmon/Library/CloudStorage/GoogleDrive-bharm257@gmail.com/My Drive/Family_Photos_25_Scans copy/photos_ending_in_a'

    def __init__(self, overwrite_files: bool = False):
        self.detector = dlib.get_frontal_face_detector()
        self.overwrite_files = overwrite_files
        logger.info(f"Rotator initialized. Overwrite files: {self.overwrite_files}")

        # We'll store a reference to an ApprovalWindow (created in main).
        self.approval_window = None

    def analyze_images(self):
        """
        Recursively loop through all files and subdirectories,
        looking for images to analyze and rotate.
        """
        images = []
        for root_dir, sub_dir, files in os.walk(self.IMAGES_DIRECTORY):
            for file_name in files:
                if file_name.lower().endswith((".jpeg", ".jpg", ".png")):
                    base_name, extension = os.path.splitext(file_name)
                    # Exclude anything ending with "_b"
                    if not base_name.endswith("_b"):
                        file_path = os.path.join(root_dir, file_name)
                        images.append(file_path)

        logger.info(f"Found {len(images)} image(s) in {self.IMAGES_DIRECTORY}.")

        with click.progressbar(images, label=f"Analyzing {len(images)} Images...") as filepaths:
            for filepath in filepaths:
                image = self.open_image(filepath)
                if image is None:
                    continue

                # If faces are detected at cycle>0, that image is queued for approval
                rotation = self.analyze_image(image, filepath)
                # "rotation" is the number of degrees if a non-zero rotation was found;
                # 0 means no rotation was performed (i.e., no queueing).

        logger.info("Done analyzing images.")

    def analyze_image(self, image: ImageFile, filepath: str) -> int:
        """
        Matches the console logic:
         - 4 cycles (0°, 90°, 180°, 270°)
         - If faces appear at cycle > 0, propose a rotation
         - If cycle == 0 finds faces, do nothing
        """
        original_image = image.copy()  # Keep an unrotated copy to show side-by-side

        for cycle in range(4):
            if cycle > 0:
                image = image.rotate(90, expand=True)
                logger.debug(f"Rotating '{filepath}' by 90 degrees (attempt #{cycle}).")

            image_copy = np.asarray(image)
            image_gray = cv2.cvtColor(image_copy, cv2.COLOR_BGR2GRAY)
            faces = self.detector(image_gray, 0)
            if len(faces) == 0:
                logger.debug(f"No faces found in '{filepath}' at rotation #{cycle}.")
                continue

            # If faces are detected at cycle == 0, do nothing (per your console logic).
            if cycle == 0:
                logger.debug(
                    f"Faces found at 0° in '{filepath}', skipping rotation (per console logic)."
                )
                return 0

            # If faces are detected at cycle > 0, propose that rotation in the GUI.
            degrees = cycle * 90
            logger.info(f"Faces found in '{filepath}'. Proposed rotation: {degrees}°.")

            if self.approval_window:
                self.approval_window.queue_item(original_image, image, filepath, degrees)
            return degrees

        return 0

    def open_image(self, filepath: str) -> ImageFile:
        """Open and scale down the image using Pillow."""
        try:
            image = Image.open(filepath)
            logger.debug(f"Image '{filepath}' opened successfully.")
            # Scale the image down to reduce memory usage
            MAX_DIMENSION = 1600
            image.thumbnail((MAX_DIMENSION, MAX_DIMENSION), Image.Resampling.LANCZOS)
            return image
        except Exception as e:
            logger.error(f"Error opening image '{filepath}': {e}")
            return None

    def save_image(self, image: ImageFile, filepath: str) -> bool:
        """Save the rotated (already scaled) image using Pillow by overwriting the original file."""
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
    """
    A simple 'main' entry point for the PyQt application.
    We create a QApplication, the Rotator, the ApprovalWindow, and start analyzing.
    """
    qt_app = QtWidgets.QApplication(sys.argv)

    rotator = Rotator(overwrite_files)
    approval_window = ApprovalWindow(rotator)
    rotator.approval_window = approval_window

    # Optionally show the window right away
    approval_window.show()
    logger.info("Approval window should now be visible.")
    approval_window.queue_item(Image.new("RGB", (200, 200)), Image.new("RGB", (200, 200)), "test.jpg", 90)

    # Use a thread to do the image analysis so we don't block the GUI
    from threading import Thread

    def analyze_in_background():
        rotator.analyze_images()

    thread = Thread(target=analyze_in_background)
    thread.start()

    # Launch the Qt event loop
    logger.info("Starting PyQt event loop...")
    sys.exit(qt_app.exec_())

if __name__ == "__main__":
    cli()