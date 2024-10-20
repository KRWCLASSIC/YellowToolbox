# External Imports
from pathlib import Path
from tqdm import tqdm
import requests
import zipfile
import shutil
import os
import toml

# Function to normalize line endings
def normalize_line_endings(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        return f.read().replace('\r\n', '\n')

# Function to compare files
def files_are_different(file1, file2):
    ext1 = file1.suffix.lower()
    ext2 = file2.suffix.lower()

    if ext1 in ['.py', '.txt', '.md', '.ini', '.gitignore', '.json'] and \
       ext2 in ['.py', '.txt', '.md', '.ini', '.gitignore', '.json']:
        return normalize_line_endings(file1) != normalize_line_endings(file2)
    else:
        with open(file1, 'rb') as f1, open(file2, 'rb') as f2:
            return f1.read() != f2.read()

# Function to update TOML file
def update_toml_file(latest_file, local_file):
    with open(latest_file, 'r') as f:
        latest_config = toml.load(f)
    
    with open(local_file, 'r') as f:
        local_config = toml.load(f)

    def update_dict(latest, local):
        for key, value in latest.items():
            if isinstance(value, dict):
                node = local.setdefault(key, {})
                update_dict(value, node)
            else:
                local.setdefault(key, value)

    update_dict(latest_config, local_config)

    with open(local_file, 'w') as f:
        toml.dump(local_config, f)

# Main update function
def update():
    url = "https://github.com/KRWCLASSIC/YellowToolbox/archive/refs/heads/main.zip"
    
    response = requests.get(url, stream=True, timeout=10)
    total_size = int(response.headers.get('content-length', 0))

    with open("latest.zip", "wb") as file:
        progress_bar = tqdm(total=total_size, unit='B', unit_scale=True, desc="Downloading")
        
        for data in response.iter_content(chunk_size=4096):
            file.write(data)
            progress_bar.update(len(data))
    
    progress_bar.close()
    
    with zipfile.ZipFile("latest.zip", "r") as zip_ref:
        zip_ref.extractall("latest_version")
    
    latest_dir = Path("latest_version/YellowToolbox-main")
    local_dir = Path(os.getcwd())
    
    for root, _, files in os.walk(latest_dir):
        for file_name in files:
            latest_file = Path(root) / file_name
            relative_path = latest_file.relative_to(latest_dir)
            local_file = local_dir / relative_path
            
            if not local_file.exists():
                local_file.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(latest_file, local_file)
            else:
                if relative_path.name == "config.toml":
                    update_toml_file(latest_file, local_file)
                else:
                    if files_are_different(latest_file, local_file):
                        shutil.copy2(latest_file, local_file)
                        print(f"Updated: {relative_path}")

    shutil.rmtree("latest_version")
    os.remove("latest.zip")
    
    print("Update completed. Restart the script to apply changes.")
