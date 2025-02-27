import os
import re
import csv
import datetime
import logging
from PIL import Image, ExifTags

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def natural_keys(text):
    """
    Helper to turn a string into a list of string/number chunks for natural sorting.
    Example: "1997_September_0010" -> ["1997_September_", 10, ""]
    """
    def atoi(t):
        return int(t) if t.isdigit() else t
    return [atoi(c) for c in re.split(r'(\d+)', text)]

def get_decimal_from_dms(dms, ref):
    """Convert degrees, minutes, seconds to decimal."""
    try:
        degrees = dms[0][0] / dms[0][1]
        minutes = dms[1][0] / dms[1][1]
        seconds = dms[2][0] / dms[2][1]
        dec = degrees + minutes / 60 + seconds / 3600
        if ref in ['S', 'W']:
            dec = -dec
        return dec
    except Exception as e:
        logging.exception("Error converting DMS to decimal: %s", e)
        return None

def extract_gps_info(exif_data):
    """Extract GPS info from EXIF data if available."""
    if "GPSInfo" in exif_data:
        gps_info = {}
        for key in exif_data["GPSInfo"]:
            decoded = ExifTags.GPSTAGS.get(key, key)
            gps_info[decoded] = exif_data["GPSInfo"][key]
        if ("GPSLatitude" in gps_info and "GPSLatitudeRef" in gps_info and
            "GPSLongitude" in gps_info and "GPSLongitudeRef" in gps_info):
            lat = get_decimal_from_dms(gps_info["GPSLatitude"], gps_info["GPSLatitudeRef"])
            lon = get_decimal_from_dms(gps_info["GPSLongitude"], gps_info["GPSLongitudeRef"])
            return f"Latitude: {lat}, Longitude: {lon}"
    return ""

def get_exif_data(image):
    """Extract EXIF data from an image."""
    exif = {}
    try:
        info = image._getexif()
        if info:
            for tag, value in info.items():
                decoded = ExifTags.TAGS.get(tag, tag)
                exif[decoded] = value
    except Exception as e:
        logging.exception("Error getting EXIF data: %s", e)
    return exif

def process_file(file_path, file, root):
    """Process an individual file and return a row dictionary with its metadata."""
    name, ext = os.path.splitext(file)
    # Determine photo type based on naming convention
    if name.endswith('_a'):
        photo_type = "Enhanced"
    elif name.endswith('_b'):
        photo_type = "Back"
    else:
        photo_type = "Original"

    # File system timestamps
    try:
        ctime = os.path.getctime(file_path)
        mtime = os.path.getmtime(file_path)
        date_created = datetime.datetime.fromtimestamp(ctime).strftime('%Y-%m-%d %H:%M:%S')
        date_modified = datetime.datetime.fromtimestamp(mtime).strftime('%Y-%m-%d %H:%M:%S')
    except Exception as e:
        logging.exception("Error getting file times for %s: %s", file_path, e)
        date_created = ""
        date_modified = ""

    file_size = os.path.getsize(file_path)
    date_taken = ""
    dimensions = ""
    camera_info_str = ""
    gps_data = ""

    # Open the image to extract dimensions and EXIF metadata
    try:
        with Image.open(file_path) as img:
            dimensions = f"{img.width}x{img.height}"
            exif_data = get_exif_data(img)
            if exif_data:
                date_taken = exif_data.get("DateTimeOriginal", "")
                camera_info = []
                if "Make" in exif_data:
                    camera_info.append("Make: " + str(exif_data["Make"]))
                if "Model" in exif_data:
                    camera_info.append("Model: " + str(exif_data["Model"]))
                if "ExposureTime" in exif_data:
                    camera_info.append("ExposureTime: " + str(exif_data["ExposureTime"]))
                if "FNumber" in exif_data:
                    camera_info.append("FNumber: " + str(exif_data["FNumber"]))
                if "ISOSpeedRatings" in exif_data:
                    camera_info.append("ISO: " + str(exif_data["ISOSpeedRatings"]))
                camera_info_str = "; ".join(camera_info)
                gps_data = extract_gps_info(exif_data)
    except Exception as e:
        logging.exception("Error processing image %s: %s", file_path, e)

    # Use the immediate parent folder as album/collection name
    album_name = os.path.basename(root)

    row = {
        "File Name": file,
        "Full File Path": file_path,
        "Photo Type": photo_type,
        "Date Created": date_created,
        "Date Modified": date_modified,
        "Date Taken": date_taken,
        "File Extension": ext.lower(),
        "File Size": file_size,
        "Dimensions": dimensions,
        "Folder/Album Name": album_name,
        "Camera Model/Settings": camera_info_str,
        "Location/GPS Data": gps_data
    }
    return row

def process_and_append_photos(base_directory, output_csv):
    """
    1. Groups related photos (Original, Enhanced, Back) by base name.
    2. Sorts them naturally by directory and base name.
    3. Writes them in the order: Original, Enhanced, Back.
    4. Ensures that duplicate rows (by file path) are not written across multiple runs.
    """
    allowed_extensions = {'.jpg', '.jpeg', '.png', '.tiff', '.bmp'}
    fieldnames = [
        "File Name", "Full File Path", "Photo Type", "Date Created", "Date Modified",
        "Date Taken", "File Extension", "File Size", "Dimensions",
        "Folder/Album Name", "Camera Model/Settings", "Location/GPS Data"
    ]
    # groups: key = (root, base_key)
    #         value = dict with possible keys "Original", "Enhanced", "Back"
    groups = {}

    # Walk through the directory recursively
    for root, dirs, files in os.walk(base_directory):
        logging.info("Processing directory: %s (found %d files)", root, len(files))
        # Sort the files alphabetically before grouping
        for file in sorted(files):
            name, ext = os.path.splitext(file)
            if ext.lower() not in allowed_extensions:
                continue

            file_path = os.path.join(root, file)
            # Compute a group key: remove trailing _a or _b if present
            if name.endswith('_a') or name.endswith('_b'):
                base_key = name[:-2]
            else:
                base_key = name

            group_key = (root, base_key)
            if group_key not in groups:
                groups[group_key] = {}

            row = process_file(file_path, file, root)
            # This will override any duplicate type entries in the same group,
            # ensuring we only keep one row per type.
            groups[group_key][row["Photo Type"]] = row
            logging.info("Processed file: %s", file_path)

    # --- SORT THE GROUPS NATURALLY ---
    def group_sort_key(k):
        # k is (root, base_key)
        root_part, base_key_part = k
        return (natural_keys(root_part), natural_keys(base_key_part))

    sorted_group_keys = sorted(groups.keys(), key=group_sort_key)

    # Initialize seen_paths set from existing CSV file to avoid duplicates across runs
    seen_paths = set()
    if os.path.exists(output_csv):
        with open(output_csv, mode='r', newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                seen_paths.add(row["Full File Path"])

    # Open the CSV file in append mode (or create it if it doesn't exist)
    file_exists = os.path.exists(output_csv)
    mode = 'a' if file_exists else 'w'
    with open(output_csv, mode=mode, newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()
            logging.info("CSV header written to %s", output_csv)

        # For each group, write the rows in order: Original, Enhanced, Back
        for group_key in sorted_group_keys:
            group = groups[group_key]
            for ptype in ["Original", "Enhanced", "Back"]:
                if ptype in group:
                    row = group[ptype]
                    if row["Full File Path"] not in seen_paths:
                        writer.writerow(row)
                        seen_paths.add(row["Full File Path"])
            csvfile.flush()

    logging.info("Completed processing all photos. Spreadsheet updated: %s", output_csv)

if __name__ == '__main__':
    base_directory = '/Users/bryceharmon/Desktop/Family Photos copy'
    output_csv = "photo_data.csv"
    logging.info("Script started.")
    process_and_append_photos(base_directory, output_csv)
    logging.info("Script finished.")