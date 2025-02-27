import csv
import os


def create_initial_csv(file_path):
    fieldnames = [
        "File Name", "Full File Path", "Photo Type", "Date Created", "Date Modified",
        "Date Taken", "File Extension", "File Size", "Dimensions",
        "Folder/Album Name", "Camera Model/Settings", "Location/GPS Data"
    ]

    # Check if the file already exists
    if os.path.exists(file_path):
        print(f"{file_path} already exists.")
        return

    # Create the CSV file and write the header row
    with open(file_path, mode="w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

    print(f"Created CSV file: {file_path}")


if __name__ == "__main__":
    output_csv = "photo_data.csv"  # You can change the file name or path if desired
    create_initial_csv(output_csv)