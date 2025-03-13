import os
import piexif
from PIL import Image
from datetime import datetime

# Hardcoded folder path:
FOLDER_PATH = "/Users/bryceharmon/Library/CloudStorage/GoogleDrive-bharm257@gmail.com/My Drive/Family_Photos_25_Scans/2005_April_23"


def parse_month_year_from_folder(folder_name):
    """
    Expects folder_name in the format 'YYYY_MonthName_DD'
    e.g. '2002_July_08'

    We will ignore the day portion and assume '01' as the day.
    Returns a datetime object for the first of that month.
    """
    parts = folder_name.split('_')

    if len(parts) != 3:
        raise ValueError("Folder name not in expected format 'YYYY_MonthName_DD'")

    year_str, month_str, _day_str = parts

    # You can expand/modify this for your local language or abbreviations
    month_map = {
        'January': 1, 'Jan': 1,
        'February': 2, 'Feb': 2,
        'March': 3, 'Mar': 3,
        'April': 4, 'Apr': 4,
        'May': 5,
        'June': 6, 'Jun': 6,
        'July': 7, 'Jul': 7,
        'August': 8, 'Aug': 8,
        'September': 9, 'Sep': 9, 'Sept': 9,
        'October': 10, 'Oct': 10,
        'November': 11, 'Nov': 11,
        'December': 12, 'Dec': 12
    }

    # Convert strings to year, month
    year = int(year_str)
    if month_str not in month_map:
        raise ValueError(f"Unrecognized month '{month_str}'. Please update 'month_map'.")
    month = month_map[month_str]

    # We'll ignore the actual day in the folder and just default to the 1st
    day = 1

    # Create the datetime object at 12:00:00 (noon) by default
    return datetime(year, month, day, 12, 0, 0)


def set_exif_datetime(image_path, new_datetime):
    """
    Sets the EXIF 'DateTimeOriginal' for the given image to new_datetime.
    Uses piexif to handle the EXIF data.
    """
    exif_time_str = new_datetime.strftime("%Y:%m:%d %H:%M:%S")

    # Attempt to load existing EXIF; if none, create a default dict
    try:
        exif_dict = piexif.load(image_path)
    except Exception:
        exif_dict = {"0th": {}, "Exif": {}, "GPS": {}, "1st": {}, "thumbnail": None}

    # Set DateTimeOriginal
    exif_dict["Exif"][piexif.ExifIFD.DateTimeOriginal] = exif_time_str.encode("utf-8")
    # Set DateTimeDigitized (optional)
    exif_dict["Exif"][piexif.ExifIFD.DateTimeDigitized] = exif_time_str.encode("utf-8")
    # Set primary DateTime (shown by some file explorers)
    exif_dict["0th"][piexif.ImageIFD.DateTime] = exif_time_str.encode("utf-8")

    # Convert back to binary EXIF data
    exif_bytes = piexif.dump(exif_dict)

    # Save image with updated EXIF
    image = Image.open(image_path)
    image.save(image_path, exif=exif_bytes)


def main():
    # Extract month/year from folder name
    folder_name = os.path.basename(FOLDER_PATH)
    date_from_folder = parse_month_year_from_folder(folder_name)

    # Loop through each file in the folder
    for filename in os.listdir(FOLDER_PATH):
        file_path = os.path.join(FOLDER_PATH, filename)

        # Check if it's a file and if extension is an image
        if os.path.isfile(file_path) and filename.lower().endswith(
                ('.jpg', '.jpeg', '.png', '.tif', '.tiff')
        ):
            print(f"Processing {file_path}")
            try:
                set_exif_datetime(file_path, date_from_folder)
                # Print only year/month to reflect ignoring the actual day
                print(f"  EXIF date updated to {date_from_folder.strftime('%Y-%m')}")
            except Exception as e:
                print(f"  Could not update EXIF for {file_path}. Error: {e}")


if __name__ == "__main__":
    main()