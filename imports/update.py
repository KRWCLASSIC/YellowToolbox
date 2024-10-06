# External Imports
from pathlib import Path
from tqdm import tqdm
import configparser
import requests
import hashlib
import zipfile
import shutil
import os

def files_are_different(file1, file2):
    """Compare two files based on their contents."""
    with open(file1, 'rb') as f1, open(file2, 'rb') as f2:
        return f1.read() != f2.read()

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
                # Compare file contents
                if files_are_different(latest_file, local_file):
                    shutil.copy2(latest_file, local_file)
                    print(f"Updated: {relative_path}")
                else:
                    print(f'{relative_path} remained unchanged.')

    # Cleanup
    shutil.rmtree("latest_version")
    os.remove("latest.zip")
    
    print("Update completed. Restart the script to apply changes.")