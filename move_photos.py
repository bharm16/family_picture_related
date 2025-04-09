import os
import shutil

def move_photos_ending_in_a(source_dir):
    """
    Walk through 'source_dir' recursively and move any files
    whose base name ends with '_a' to a single, top-level directory
    called 'photos_ending_in_a'.
    """
    # Create the top-level destination folder
    target_dir = os.path.join(source_dir, "photos_ending_in_a")
    os.makedirs(target_dir, exist_ok=True)

    # Walk through the directory tree
    for root, dirs, files in os.walk(source_dir):
        # Skip the target directory itself to avoid moving files in a loop
        if os.path.abspath(root) == os.path.abspath(target_dir):
            continue

        for filename in files:
            name, ext = os.path.splitext(filename)
            # Check if the base name ends with '_a'
            if name.endswith("_a"):
                src_path = os.path.join(root, filename)
                dst_path = os.path.join(target_dir, filename)
                # Move the file
                shutil.move(src_path, dst_path)
                print(f"Moved: {src_path} -> {dst_path}")

if __name__ == "__main__":
    # Replace the directory path below with your own
    directory = r"/Users/bryceharmon/Family_Photos_25_Scans_copy_ad"
    move_photos_ending_in_a(directory)