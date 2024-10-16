# External Imports
from pathlib import Path
from tqdm import tqdm
import configparser
import requests
import zipfile
import shutil
import os

# Converting from CRLF to LF (github vs windows)
def normalize_line_endings(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        return f.read().replace('\r\n', '\n')  # Replace CRLF with LF

# Compare files
def files_are_different(file1, file2):
    # Get the file extensions
    ext1 = file1.suffix.lower()
    ext2 = file2.suffix.lower()

    # If both files are text files, normalize and compare their contents
    if ext1 in ['.py', '.txt', '.md', '.ini', '.gitignore', '.json'] and \
       ext2 in ['.py', '.txt', '.md', '.ini', '.gitignore', '.json']:
        return normalize_line_endings(file1) != normalize_line_endings(file2)
    else:
        # For binary files, compare their contents byte by bytel
        with open(file1, 'rb') as f1, open(file2, 'rb') as f2:
            return f1.read() != f2.read()

# Function to update config.ini without overriding existing values
def update_config_file(latest_file, local_file):
    config = configparser.ConfigParser()
    config.read(local_file)

    latest_config = configparser.ConfigParser()
    latest_config.read(latest_file)

    # Iterate over sections in the latest config
    for section in latest_config.sections():
        if not config.has_section(section):
            config.add_section(section)
        
        # Add keys from the latest config if they don't exist in the local config
        for key, value in latest_config.items(section):
            if not config.has_option(section, key):
                config.set(section, key, value)

    # Remove keys from the local config that are not in the latest config
    for section in config.sections():
        if latest_config.has_section(section):
            for key in config.options(section):
                if not latest_config.has_option(section, key):
                    config.remove_option(section, key)

    with open(local_file, 'w') as configfile:
        config.write(configfile)

# Update
def update():
    url = "https://github.com/KRWCLASSIC/YellowToolbox/archive/refs/heads/main.zip"
    
    # Send a GET request
    response = requests.get(url, stream=True, timeout=10)
    total_size = int(response.headers.get('content-length', 0))  # Get the total file size

    with open("latest.zip", "wb") as file:
        # Create a progress bar using tqdm
        progress_bar = tqdm(total=total_size, unit='B', unit_scale=True, desc="Downloading")
        
        for data in response.iter_content(chunk_size=4096):
            file.write(data)
            progress_bar.update(len(data))  # Update the progress bar with the size of the chunk
    
    progress_bar.close()  # Close the progress bar when done
    
    # Extract ZIP
    with zipfile.ZipFile("latest.zip", "r") as zip_ref:
        zip_ref.extractall("latest_version")
    
    latest_dir = Path("latest_version/YellowToolbox-main")  # Path to the extracted folder
    local_dir = Path(os.getcwd())  # Current working directory
    
    # Compare and update files
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
                # Special handling for config.ini
                if relative_path.name == "config.ini":
                    update_config_file(latest_file, local_file)
                else:
                    # Compare file contents using the updated function
                    if files_are_different(latest_file, local_file):
                        shutil.copy2(latest_file, local_file)
                        print(f"Updated: {relative_path}")

    # Cleanup
    shutil.rmtree("latest_version")
    os.remove("latest.zip")
    
    print("Update completed. Restart the script to apply changes.")