import os
import requests
import zipfile

def download_dataset():
    """
    Instructions for downloading the Parkinson's Disease IMU Dataset.
    Original Source: [Insert URL if known, e.g., Zenodo / Harvard Dataverse]
    
    This script is a placeholder to document the data acquisition process.
    The dataset is too large (~3.7GB) to be hosted on GitHub.
    """
    data_dir = os.path.join(os.getcwd(), 'data', 'raw')
    os.makedirs(data_dir, exist_ok=True)
    
    print("--- Dataset Download Guide ---")
    print("1. Download the 'PD_IMU_Data.zip' from the official repository.")
    print("2. Place the zip file in: " + data_dir)
    print("3. Run the processing script: python src/data_processing/clean_data.py")
    print("-------------------------------")

if __name__ == "__main__":
    download_dataset()
