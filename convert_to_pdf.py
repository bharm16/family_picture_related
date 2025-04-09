import os
from PIL import Image
from tqdm import tqdm

# Disable PIL's decompression bomb protection for large images
Image.MAX_IMAGE_PIXELS = None

input_dir = r'/Users/bryceharmon/Family_Photos_25_Scans_copy_ad/photos_ending_in_a'
output_dir = r'/Users/bryceharmon/photo_pdfs'

os.makedirs(output_dir, exist_ok=True)

valid_extensions = ['.jpeg', '.jpg', '.png', '.tif', '.tiff']
image_files = [f for f in os.listdir(input_dir)
               if os.path.splitext(f.lower())[1] in valid_extensions]

for image_file in tqdm(image_files, desc='Converting images to PDF'):
    image_path = os.path.join(input_dir, image_file)
    image = Image.open(image_path).convert('RGB')

    # Explicitly preserve original filename
    pdf_filename = os.path.splitext(image_file)[0] + '.pdf'
    output_path = os.path.join(output_dir, pdf_filename)

    image.save(output_path, 'PDF')