import subprocess

# Download CYGNSS data
subprocess.run(['download.sh'], shell=True, cwd='Global')
