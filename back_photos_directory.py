#!/usr/bin/env python3
import os
import shutil

# Define the source directory (where your original photos are)
src_dir = "/Users/bryceharmon/Documents/family_photos_copy/Original"

# Define the destination directory (where you'll store the back photos)
dst_dir = "/Users/bryceharmon/Documents/family_photos_copy/BackPhotos"

# Create the destination directory if it does not exist
if not os.path.exists(dst_dir):
    os.makedirs(dst_dir)

# Walk through the source directory recursively
for root, dirs, files in os.walk(src_dir):
    for file in files:
        # Split filename and extension
        name, ext = os.path.splitext(file)
        # Check if the file's base name ends with '_b'
        if name.endswith('_b'):
            src_file = os.path.join(root, file)
            dst_file = os.path.join(dst_dir, file)
            shutil.copy2(src_file, dst_file)
            print(f"Copied: {src_file} to {dst_file}")