#!/bin/bash
# stop on error
set -e

source docker-name.sh

# Extract the base name and tag
base_name=$(echo $image_name | cut -d':' -f1)
tag=$(echo $image_name | cut -d':' -f2)

# Build the base image
docker build -f Dockerfile.base -t "${base_name}-base:${tag}" .

# If the image type is with_pytorch, build the PyTorch image
if [[ $image_name == *"with_pytorch"* ]]; then
    docker build --build-arg BASE_IMAGE="${base_name}-base:${tag}" -f Dockerfile.pytorch -t "$image_name" .
else
    # For the default image, we just tag the base image
    docker tag "${base_name}-base:${tag}" "$image_name"
fi

echo "Built image: $image_name"
