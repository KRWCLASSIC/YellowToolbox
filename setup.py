import os
import subprocess

# Define the files to be created
files_to_create = ['files/ban.txt', 'files/telemetry.json', 'files/token.txt']

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
with open('files/token.txt', 'w') as f:
    f.write(token)
print("Token saved to files/token.txt")

# Check and install required packages
def install_packages():
    with open('files/requirements.txt', 'r') as f:
        packages = f.read().splitlines()
    
    for package in packages:
        try:
            subprocess.check_call(['pip', 'show', package])
            print(f"{package} is already installed.")
        except subprocess.CalledProcessError:
            print(f"{package} is not installed. Installing...")
            subprocess.check_call(['pip', 'install', package])

install_packages()