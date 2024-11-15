import boto3
import json
import openai
from pinecone import Pinecone, ServerlessSpec
from pathlib import Path
import os

# Configuration Section
# Configuration Section - Replace these variables or use TOML for secure handling
PINECONE_API_KEY = ''
OPENAI_API_KEY = ''
S3_BUCKET_NAME = 'team9-project4'
S3_FOLDER_PATH = 'output_json/'  # Path to the folder containing JSON files in S3
INDEX_NAME = 'team9-project4-vector'

# Initialize Pinecone and OpenAI
openai.api_key = OPENAI_API_KEY
pc = Pinecone(api_key=PINECONE_API_KEY)
if INDEX_NAME not in pc.list_indexes().names():
    pc.create_index(
        name=INDEX_NAME,
        dimension=1536,
        metric='cosine',
        spec=ServerlessSpec(cloud='aws', region='us-west-2')
    )
index = pc.Index(INDEX_NAME)

# Initialize AWS S3 Client
s3_client = boto3.client('s3')

def list_json_files_in_s3(bucket_name: str, folder_path: str):
    """List all JSON files in a specific S3 folder."""
    response = s3_client.list_objects_v2(Bucket=bucket_name, Prefix=folder_path)
    return [item['Key'] for item in response.get('Contents', []) if item['Key'].endswith('.json')]

def download_json_from_s3(bucket_name: str, s3_key: str, download_path: Path):
    """Download JSON file from S3 bucket."""
    s3_client.download_file(bucket_name, s3_key, str(download_path))
    print(f"Downloaded {s3_key} from S3 bucket {bucket_name} to {download_path}.")

def generate_embedding(text: str):
    """Generate embedding for a given text using OpenAI."""
    response = openai.Embedding.create(input=text, model="text-embedding-ada-002")
    embedding = response['data'][0]['embedding']
    return embedding

def process_and_upload_to_pinecone(json_path: Path, document_name: str):
    """Process JSON file and upload embeddings to Pinecone with additional metadata."""
    with open(json_path, 'r') as f:
        data = json.load(f)

        for page in data:
            text_content = page.get('contents', "No Text Available")
            table_data = page.get('cells', [])
            image_data = page.get('image', {}).get('bytes', None)

            # Generate embedding for text content
            embedding = generate_embedding(text_content)

            # Serialize table data into a JSON string
            table_json = json.dumps(table_data) if table_data else "No Table Data"

            # Prepare metadata
            metadata = {
                "document": document_name,
                "page_num": page["extra"].get("page_num", "Unknown Page"),
                "title": document_name,
                "author": page.get("author", "Unknown Author"),
                "text_preview": text_content[:1000] if isinstance(text_content, str) else "No Preview Available",
                "table": table_json,
            }

            # Only include image data if available
            if image_data:
                metadata["image"] = "Image data available"

            # Print metadata for verification
            print(f"Uploading with metadata preview: {json.dumps(metadata, indent=4)[:1000]}...")

            # Upload to Pinecone
            index.upsert([(f"{document_name}_{metadata['page_num']}", embedding, metadata)])
            print(f"Uploaded page {metadata['page_num']} from {document_name} to Pinecone.")

def main():
    """Main function to process all JSON files from S3 folder."""
    # List all JSON files in the S3 folder
    json_files = list_json_files_in_s3(S3_BUCKET_NAME, S3_FOLDER_PATH)
    print(f"Found JSON files: {json_files}")

    # Temporary local directory for downloading JSON files
    temp_dir = Path("./temp_json_files")
    temp_dir.mkdir(exist_ok=True)

    for s3_key in json_files:
        # Extract document name from S3 key
        document_name = Path(s3_key).stem.replace("_", " ")

        # Define local path for download
        local_path = temp_dir / f"{document_name}.json"

        # Download JSON file from S3
        download_json_from_s3(S3_BUCKET_NAME, s3_key, local_path)

        # Process and upload to Pinecone
        process_and_upload_to_pinecone(local_path, document_name)

        # Optionally delete the local file to save space
        local_path.unlink()

if __name__ == "__main__":
    main()
