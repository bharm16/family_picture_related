import sys
import os
import logging
import cv2
import dlib
import numpy as np
import json
from PyQt5.QtCore import pyqtSignal
from PIL import Image, ImageFile
Image.MAX_IMAGE_PIXELS = None
from PyQt5 import QtWidgets, QtGui, QtCore
import click

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ApprovalWindow(QtWidgets.QWidget):
    queue_item_signal = pyqtSignal(object, object, str, int)

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

        self.queue_item_signal.connect(self.queue_item)

    def queue_item(self, original_image, rotated_image, filepath, degrees):
        logger.info(f"Queueing image for approval: {filepath}, proposed rotation: {degrees}°")
        self.queue.append((original_image, rotated_image, filepath, degrees))
        if self.current_item is None:
            self.show_next_item()

    def show_next_item(self):
        if self.current_item:
            self.current_item.deleteLater()
            self.current_item = None

        if self.queue:
            item = self.queue.pop(0)
            self.display_item(*item)
        else:
            for i in reversed(range(self.item_layout.count())):
                widget_to_remove = self.item_layout.itemAt(i).widget()
                if widget_to_remove:
                    widget_to_remove.setParent(None)

    def display_item(self, original_image, rotated_image, filepath, degrees):
        self.current_item = QtWidgets.QWidget()
        self.current_filepath = filepath  # explicitly store filepath
        v_layout = QtWidgets.QVBoxLayout(self.current_item)

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

        buttons_layout = QtWidgets.QHBoxLayout()
        approve_button = QtWidgets.QPushButton("Approve")
        reject_button = QtWidgets.QPushButton("Reject")
        buttons_layout.addWidget(approve_button)
        buttons_layout.addWidget(reject_button)

        v_layout.addLayout(buttons_layout)

        approve_button.clicked.connect(lambda: self.on_approve(filepath, rotated_image))
        reject_button.clicked.connect(self.on_reject)

        for i in reversed(range(self.item_layout.count())):
            widget_to_remove = self.item_layout.itemAt(i).widget()
            if widget_to_remove:
                widget_to_remove.setParent(None)
        self.item_layout.addWidget(self.current_item)

    def on_approve(self, filepath, rotated_image):
        logger.info(f"Image approved: {filepath}, saving rotated image.")
        self.rotator.save_image(rotated_image, filepath)
        self.rotator.save_processed_image(filepath)
        self.show_next_item()

    def on_reject(self):
        logger.info(f"Image rotation rejected: {self.current_filepath}")
        if self.current_filepath:
            self.rotator.save_processed_image(self.current_filepath)
            self.show_next_item()

    def pil2pixmap(self, pil_image):
        if pil_image.mode != "RGB":
            pil_image = pil_image.convert("RGB")
        display_img = pil_image.copy()
        display_img.thumbnail((400, 400))
        data = display_img.tobytes("raw", "RGB")
        bytes_per_line = display_img.width * 3
        qimage = QtGui.QImage(data, display_img.width, display_img.height, bytes_per_line, QtGui.QImage.Format_RGB888)
        return QtGui.QPixmap.fromImage(qimage)

class Rotator:
    IMAGES_DIRECTORY = '/Users/bryceharmon/Family_Photos_25_Scans_copy_ad/photos_ending_in_a copy'

    def __init__(self, overwrite_files: bool = False):
        self.detector = dlib.get_frontal_face_detector()
        self.overwrite_files = overwrite_files
        self.processed_images = 'processed_images.json'
        self.processed_images_set = self.load_processed_images()
        self.approval_window = None
        logger.info(f"Rotator initialized. Overwrite files: {self.overwrite_files}")

    def load_processed_images(self):
        if os.path.exists(self.processed_images):
            with open(self.processed_images, 'r') as f:
                return set(json.load(f))
        return set()

    def save_processed_image(self, filepath):
        self.processed_images_set.add(filepath)
        with open(self.processed_images, 'w') as f:
            json.dump(list(self.processed_images_set), f)

    def analyze_images(self):
        logger.info("Starting image analysis...")
        images = []
        for root_dir, sub_dir, files in os.walk(self.IMAGES_DIRECTORY):
            for file_name in files:
                if file_name.lower().endswith((".jpeg", ".jpg", ".png")):
                    base_name, extension = os.path.splitext(file_name)
                    if not base_name.endswith("_b"):
                        file_path = os.path.join(root_dir, file_name)
                        if file_path not in self.processed_images_set:
                            images.append(file_path)

        total_images = len(images)
        logger.info(f"Found {total_images} image(s) to analyze.")
        with click.progressbar(images, label=f"Analyzing {total_images} Images...") as filepaths:
            for i, filepath in enumerate(filepaths, start=1):
                logger.info(f"Analyzing image {i}/{total_images}: {filepath}")
                image = self.open_image(filepath)
                if image is None:
                    continue
                rotation = self.analyze_image(image, filepath)

        logger.info("Image analysis complete.")

    def analyze_image(self, image: ImageFile, filepath: str) -> int:
        original_image = image.copy()

        for cycle in range(4):
            if cycle > 0:
                image = image.rotate(90, expand=True)
                logger.debug(f"Rotating '{filepath}' by 90 degrees (attempt #{cycle}).")

            image_gray = cv2.cvtColor(np.asarray(image), cv2.COLOR_BGR2GRAY)
            faces = self.detector(image_gray, 0)
            if len(faces) == 0:
                logger.debug(f"No faces found in '{filepath}' at rotation #{cycle}.")
                continue

            if cycle == 0:
                logger.debug(f"Faces detected in '{filepath}' with no rotation.")
                return 0

            degrees = cycle * 90
            logger.info(f"Faces found in '{filepath}'. Rotating by {degrees} degrees.")
            if self.approval_window:
                self.approval_window.queue_item_signal.emit(original_image, image, filepath, degrees)
            return degrees

        return 0

    def open_image(self, filepath: str) -> ImageFile:
        try:
            Image.MAX_IMAGE_PIXELS = None  # Temporarily disable the DecompressionBombWarning
            image = Image.open(filepath)
            return image
        except Exception as e:
            logger.error(f"Error opening image '{filepath}': {e}")
            return None

    def save_image(self, image: ImageFile, filepath: str) -> bool:
        try:
            ext = os.path.splitext(filepath)[1].lower()
            if ext in ['.jpg', '.jpeg']:
                # Save JPEG images with high quality to minimize compression
                image.save(filepath, quality=100)
            else:
                image.save(filepath)
            logger.info(f"Successfully overwrote and saved image: '{filepath}'")
            return True
        except Exception as e:
            logger.error(f"Error overwriting image '{filepath}': {e}")
            return False

@click.command()
@click.argument("overwrite_files", type=click.BOOL, default=False)
def cli(overwrite_files: bool = False):
    qt_app = QtWidgets.QApplication(sys.argv)

    rotator = Rotator(overwrite_files)
    approval_window = ApprovalWindow(rotator)
    rotator.approval_window = approval_window

    approval_window.show()

    from threading import Thread
    Thread(target=rotator.analyze_images).start()

    sys.exit(qt_app.exec_())

if __name__ == "__main__":
    cli()