import os
import subprocess

# Define the files to be created
files_to_create = ['files/important/ban.txt', 'files/misc/telemetry.json', 'files/important/token.txt']

# Create the necessary files if they don't exist
for file in files_to_create:
    if not os.path.exists(file):
        with open(file, 'w') as f:
            if file.endswith('telemetry.json'):
                f.write('{}')  # Initialize telemetry.json as an empty JSON object
            else:
                f.write('')  # Create an empty file
        print(f"Created {file}")

# Prompt the user for the token and save it to token.txt
token = input("Please enter your bot token: ")
with open('files/important/token.txt', 'w') as f:
    f.write(token)
print("Token saved to files/important/token.txt")

# Check and install required packages
def install_packages():
    with open('files/installation/requirements.txt', 'r') as f:
        packages = f.read().splitlines()
    
    for package in packages:
        try:
            subprocess.check_call(['pip', 'show', package])
            print(f"{package} is already installed.")
        except subprocess.CalledProcessError:
            print(f"{package} is not installed. Installing...")
            subprocess.check_call(['pip', 'install', package])

install_packages()