import subprocess

# Download SMAP soil moisture data
subprocess.run(['download.sh'], shell=True, cwd='Global')