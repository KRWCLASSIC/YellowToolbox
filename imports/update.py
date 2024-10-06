# External Imports
from pathlib import Path
from tqdm import tqdm
import configparser
import requests
import hashlib
import zipfile
import shutil
import os

def calculate_file_hash(file_path):
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        # Read and update hash string value in blocks of 4K
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def update():
    # Step 2: Download the latest version
    url = "https://github.com/KRWCLASSIC/YellowToolbox/archive/refs/heads/main.zip"
    
    # Send a GET request
    response = requests.get(url, stream=True)
    total_size = int(response.headers.get('content-length', 0))  # Get the total file size

    with open("latest.zip", "wb") as file:
        # Create a progress bar using tqdm
        progress_bar = tqdm(total=total_size, unit='B', unit_scale=True, desc="Downloading")
        
        for data in response.iter_content(chunk_size=4096):
            file.write(data)
            progress_bar.update(len(data))  # Update the progress bar with the size of the chunk
    
    progress_bar.close()  # Close the progress bar when done
    
    # Step 3: Extract ZIP
    with zipfile.ZipFile("latest.zip", "r") as zip_ref:
        zip_ref.extractall("latest_version")
    
    latest_dir = Path("latest_version/YellowToolbox-main")  # Path to the extracted folder
    local_dir = Path(os.getcwd())  # Current working directory
    
    # Step 4: Compare and update files
    for root, _, files in os.walk(latest_dir):
        for file_name in files:
            latest_file = Path(root) / file_name
            relative_path = latest_file.relative_to(latest_dir)
            local_file = local_dir / relative_path
            
            if not local_file.exists():
                # Step 5: Add new files
                local_file.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(latest_file, local_file)
            else:
                # Compare file hashes
                latest_hash = calculate_file_hash(latest_file)
                local_hash = calculate_file_hash(local_file)

                print(f'Latest file: {latest_file}')
                print(f'Local file: {local_file}')

                print("Hash 1:", latest_hash, "Hash 2:", local_hash)
                
                if latest_hash != local_hash:
                    shutil.copy2(latest_file, local_file)
                    print(f"Updated: {relative_path}")
                else:
                    print(f'{relative_path} remained unchanged.')

    # Cleanup
    shutil.rmtree("latest_version")
    os.remove("latest.zip")
    
    print("Update completed. Restart the script to apply changes.")