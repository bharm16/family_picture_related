import os
import cv2
import pytesseract
import re
import numpy as np

# Directory containing images:
folder_path = "/Users/bryceharmon/Documents/family_photos_copy/back"

# Tesseract config for single-character mode:
# You can experiment with --psm 10 (“treat the image as a single character”)
# or --psm 8 (“treat the image as a single word”).
tess_config_char = (
    "--psm 10 --oem 3 "
    "-c tessedit_char_whitelist=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ/:()-<> "
)


def character_by_character_ocr(img):
    """
    Takes a preprocessed (thresholded & inverted) image with text,
    finds each connected component, and does single-character OCR on each bounding box.
    Returns a list of (x, y, w, h, text_char).
    """
    # Find external contours:
    contours, hierarchy = cv2.findContours(img, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    # List to store bounding boxes and recognized character
    boxes_and_chars = []

    for cnt in contours:
        x, y, w, h = cv2.boundingRect(cnt)
        # Optionally skip bounding boxes that are too small or too large
        if w < 3 or h < 3:
            continue

        roi = img[y:y + h, x:x + w]

        # Call Tesseract for just this small patch:
        # We expect a single character, so we pass tess_config_char with --psm 10
        char_text = pytesseract.image_to_string(roi, config=tess_config_char).strip()
        if char_text:
            boxes_and_chars.append((x, y, w, h, char_text))

    # Sort by top-to-bottom, then left-to-right:
    # This is a naive approach. We basically sort by y, then x.
    boxes_and_chars.sort(key=lambda b: (b[1], b[0]))

    return boxes_and_chars


def group_into_lines(boxes_and_chars, line_threshold=10):
    """
    Groups recognized characters into lines of text based on y-coordinates.
    'line_threshold' is how close bounding boxes' y-centers need to be to be
    considered the same text line.

    Returns a list of strings, each representing a line of recognized characters.
    """
    lines = []
    current_line = []

    if not boxes_and_chars:
        return lines

    # We'll keep track of the average "center y" of the current line
    # so we know if a new char belongs on this line or the next.
    # This is a simple approach that might need refinement if text is slanted.

    # Start with the first bounding box:
    prev_y_center = boxes_and_chars[0][1] + (boxes_and_chars[0][3] / 2)
    current_line.append(boxes_and_chars[0])

    for i in range(1, len(boxes_and_chars)):
        x, y, w, h, char_text = boxes_and_chars[i]
        y_center = y + (h / 2)
        # Compare to previous line's center
        if abs(y_center - prev_y_center) <= line_threshold:
            # same line
            current_line.append(boxes_and_chars[i])
        else:
            # new line
            # sort current line's boxes by x, then join their text
            current_line.sort(key=lambda b: b[0])
            line_str = "".join([c[4] for c in current_line])
            lines.append(line_str)

            # start a new line
            current_line = [boxes_and_chars[i]]
        prev_y_center = y_center

    # Add the final line
    if current_line:
        current_line.sort(key=lambda b: b[0])
        line_str = "".join([c[4] for c in current_line])
        lines.append(line_str)

    return lines


def process_single_image(image_path):
    """
    Reads the image, does your usual preprocessing, then
    does character-by-character OCR and returns all lines recognized.
    """
    img = cv2.imread(image_path)
    if img is None:
        return [], f"Could not read image: {image_path}"

    # Preprocessing steps:
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (3, 3), 0)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    enhanced = clahe.apply(blurred)
    resized = cv2.resize(enhanced, None, fx=3, fy=3, interpolation=cv2.INTER_CUBIC)
    _, binary = cv2.threshold(resized, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    inverted = cv2.bitwise_not(binary)
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 1))
    closed = cv2.morphologyEx(inverted, cv2.MORPH_CLOSE, kernel, iterations=1)

    # If you still want to do left/right splits, do them here,
    # or do the entire image at once. For demonstration, let's do entire image at once.

    boxes_and_chars = character_by_character_ocr(closed)
    lines = group_into_lines(boxes_and_chars, line_threshold=10)

    return lines, None


def main():
    valid_exts = (".jpg", ".jpeg", ".png", ".tif", ".tiff", ".bmp")

    for filename in sorted(os.listdir(folder_path)):
        if not filename.lower().endswith(valid_exts):
            continue

        image_path = os.path.join(folder_path, filename)
        print(f"Processing: {image_path}")

        lines, err = process_single_image(image_path)
        if err:
            print(f"  Error: {err}")
            continue

        if not lines:
            print("  No text recognized.\n")
            continue

        print("  Recognized lines:")
        for line in lines:
            print("   ", line)
        print()


if __name__ == "__main__":
    main()