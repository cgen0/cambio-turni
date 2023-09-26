#!/bin/bash

# Remove the file 'deployment-package.zip' if it exists. This will delete the old zip file.
rm deployment-package.zip

# Create a new zip file 'deployment-package.zip' containing all files with a '.py' extension in subdirectories.
zip deployment-package.zip */*.py

# Update the 'deployment-package.zip' by adding any Python files in the current directory ('*.py').
zip -g deployment-package.zip *.py

# Change the current directory to 'libs-layer'.
cd libs-layer

# Run a Docker container using the 'lambci/lambda:build-python3.8' image, mounting the current directory as '/var/task'.
# Within the container, it installs Python package dependencies defined in 'requirements.txt' to a specific path.
sudo docker run -v "$PWD":/var/task "lambci/lambda:build-python3.8" /bin/sh -c "pip3.8 install -r requirements.txt -t python/lib/python3.8/site-packages/; exit"

# Create a zip file 'libs.zip' containing the 'python' directory and its contents.
zip -r libs.zip python

# Return to the previous directory.
cd ..

# Move the 'libs.zip' file from the 'libs-layer' directory to the current directory.
mv ./libs-layer/libs.zip ./
