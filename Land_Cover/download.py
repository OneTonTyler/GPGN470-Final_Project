import subprocess

# Download MODIS Land Cover data
subprocess.run(['download.sh'], shell=True, cwd='Global')
