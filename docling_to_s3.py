import datetime
import logging
import time
from pathlib import Path
import json
import boto3
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.utils.export import generate_multimodal_pages
from docling.utils.utils import create_hash

# Configuration
S3_BUCKET_NAME = 'team9-project4'  
S3_INPUT_FOLDER = 'input_pdfs/'  
S3_OUTPUT_FOLDER = 'output_json/' 
TEMP_DOWNLOAD_DIR = Path("/Users/shubhamagarwal/Documents/Northeastern/Semester_3/project_4/POC/temp_local")  # Temporary local directory

# Initialize S3 Client
s3_client = boto3.client('s3')

# Logging configuration
_log = logging.getLogger(__name__)
IMAGE_RESOLUTION_SCALE = 2.0

def list_pdfs_from_s3(bucket_name, prefix):
    """List PDF files in the specified S3 folder."""
    response = s3_client.list_objects_v2(Bucket=bucket_name, Prefix=prefix)
    pdf_files = [obj['Key'] for obj in response.get('Contents', []) if obj['Key'].endswith('.pdf')]
    return pdf_files

def download_pdf_from_s3(bucket_name, s3_key, download_path):
    """Download a PDF file from S3 to the local path."""
    download_path.parent.mkdir(parents=True, exist_ok=True)
    s3_client.download_file(bucket_name, s3_key, str(download_path))
    _log.info(f"Downloaded {s3_key} to {download_path}")

def upload_file_to_s3(local_path, bucket_name, s3_key):
    """Upload a file from the local path to S3."""
    s3_client.upload_file(str(local_path), bucket_name, s3_key)
    _log.info(f"Uploaded {local_path} to s3://{bucket_name}/{s3_key}")

def process_pdf_to_json(input_doc_path, output_dir):
    """Process a single PDF and save output to JSON."""
    pipeline_options = PdfPipelineOptions()
    pipeline_options.images_scale = IMAGE_RESOLUTION_SCALE
    pipeline_options.generate_page_images = True

    doc_converter = DocumentConverter(
        format_options={
            InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
        }
    )

    conv_res = doc_converter.convert(input_doc_path)

    rows = []
    for (
        content_text,
        content_md,
        content_dt,
        page_cells,
        page_segments,
        page,
    ) in generate_multimodal_pages(conv_res):
        dpi = page._default_image_scale * 72

        rows.append(
            {
                "document": conv_res.input.file.name,
                "hash": conv_res.input.document_hash,
                "page_hash": create_hash(
                    conv_res.input.document_hash + ":" + str(page.page_no - 1)
                ),
                "image": {
                    "width": page.image.width,
                    "height": page.image.height,
                    "base64": page.image.tobytes().hex(),
                },
                "cells": page_cells,
                "contents": content_text,
                "contents_md": content_md,
                "contents_dt": content_dt,
                "segments": page_segments,
                "extra": {
                    "page_num": page.page_no + 1,
                    "width_in_points": page.size.width,
                    "height_in_points": page.size.height,
                    "dpi": dpi,
                },
            }
        )

    # Use the input file name (without extension) as the output file name
    output_filename = output_dir / f"{input_doc_path.stem}.json"
    with open(output_filename, "w") as json_file:
        json.dump(rows, json_file, indent=4)

    _log.info(f"Processed {input_doc_path} and saved to {output_filename}")

    return output_filename

def main():
    logging.basicConfig(level=logging.INFO)

    # List all PDF files in the S3 input folder
    pdf_files = list_pdfs_from_s3(S3_BUCKET_NAME, S3_INPUT_FOLDER)

    # Temporary directory for processing files locally
    TEMP_DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)

    for s3_key in pdf_files:
        local_pdf_path = TEMP_DOWNLOAD_DIR / Path(s3_key).name
        download_pdf_from_s3(S3_BUCKET_NAME, s3_key, local_pdf_path)

        # Define output directory in the temp location
        output_dir = TEMP_DOWNLOAD_DIR / "output"
        output_dir.mkdir(parents=True, exist_ok=True)

        # Process the PDF and generate output JSON file
        output_json_path = process_pdf_to_json(local_pdf_path, output_dir)

        # Upload the JSON file to S3 output folder
        output_s3_key = f"{S3_OUTPUT_FOLDER}{output_json_path.name}"
        upload_file_to_s3(output_json_path, S3_BUCKET_NAME, output_s3_key)

        # Clean up local files if necessary (optional)
        local_pdf_path.unlink()  # Delete the local PDF file
        output_json_path.unlink()  # Delete the local JSON file

    _log.info("All PDFs processed and uploaded to S3.")

if __name__ == "__main__":
    main()
