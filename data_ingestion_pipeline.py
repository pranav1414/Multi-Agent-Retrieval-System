from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
import subprocess
import os

# Set default arguments
default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

# Function to run a Python script
def run_script(script_path):
    try:
        subprocess.run(['python', script_path], check=True)
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Script {script_path} failed with error: {e}")

# Define the DAG
with DAG(
    'data_ingestion_pipeline',
    default_args=default_args,
    description='Pipeline to parse S3 data using Docling and upload to Pinecone',
    schedule_interval=timedelta(days=1),
    start_date=datetime(2023, 1, 1),
    catchup=False,
) as dag:

    # Task 1: Run the docling_to_s3.py script to parse data from S3
    parse_data_from_s3 = PythonOperator(
        task_id='parse_data_from_s3',
        python_callable=run_script,
        op_args=['/Users/shubhamagarwal/Documents/Northeastern/Semester_3/project_4/team9_project2/Data_Ingestion/docling_to_s3.py'],
    )

    # Task 2: Run the s3_pinecone.py script to send parsed data to Pinecone
    send_data_to_pinecone = PythonOperator(
        task_id='send_data_to_pinecone',
        python_callable=run_script,
        op_args=['/Users/shubhamagarwal/Documents/Northeastern/Semester_3/project_4/team9_project2/Data_Ingestion/s3_pinecone.py'],
    )

    # Define task dependencies
    parse_data_from_s3 >> send_data_to_pinecone
