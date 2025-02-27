import os

# Base directory containing the photos
base_directory = '/Users/bryceharmon/Library/CloudStorage/GoogleDrive-bharm257@gmail.com/My Drive/Family Photos'

# Counters for each type of photo
original_count = 0
enhanced_count = 0
back_count = 0
total_count = 0

# Define allowed image file extensions
allowed_extensions = {'.jpg', '.jpeg', '.png', '.tiff', '.bmp'}

# Walk through each folder in the directory
for root, dirs, files in os.walk(base_directory):
    for file in files:
        # Get the file extension in lowercase
        name, ext = os.path.splitext(file)
        if ext.lower() in allowed_extensions:
            total_count += 1
            # Check if the filename ends with '_a' or '_b'
            if name.endswith('_a'):
                enhanced_count += 1
            elif name.endswith('_b'):
                back_count += 1
            else:
                original_count += 1

# Print the counts
print("Original photos:", original_count)
print("Enhanced photos:", enhanced_count)
print("Back photos:", back_count)
print("Total photos:", total_count)