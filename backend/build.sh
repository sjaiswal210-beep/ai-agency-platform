#!/usr/bin/env bash
# Install ffmpeg for video stitching
apt-get update && apt-get install -y ffmpeg

# Install Python dependencies
pip install -r requirements.txt
