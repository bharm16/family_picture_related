import fitz  # PyMuPDF
import os
import pandas as pd
from tqdm import tqdm
import logging
logging.basicConfig(filename='extraction.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

input_pdf_dir = r'/Users/bryceharmon/photo_pdfs'
output_csv = 'extracted_text.csv'
logging.info("Starting text extraction from PDFs in directory: %s", input_pdf_dir)

pdf_files = [f for f in os.listdir(input_pdf_dir) if f.lower().endswith('.pdf')]

data = []

for pdf_file in tqdm(pdf_files, desc="Extracting text from PDFs"):
    pdf_path = os.path.join(input_pdf_dir, pdf_file)

    try:
        doc = fitz.open(pdf_path)
        text = ""
        for page in doc:
            text += page.get_text()

        # If you prefer having the original image filename (e.g., photo001.jpg):
        original_image_filename = os.path.splitext(pdf_file)[0] + '.jpg'

        data.append({
            'pdf_filename': pdf_file,
            'original_image_filename': original_image_filename,
            'text': text.strip()
        })

    except Exception as e:
        logging.error("Error processing %s: %s", pdf_file, e)

df = pd.DataFrame(data)
df.to_csv(output_csv, index=False)

logging.info("Extraction complete! CSV saved as %s", output_csv)