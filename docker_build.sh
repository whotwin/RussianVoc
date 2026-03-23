#!/bin/bash
set -e
ANDROID_SDK=/home/hty/android-sdk
PROJECT_DIR=/mnt/d/Development
CONTAINER_SDK=/root/.buildozer

# Accept all prompts
yes | docker run --rm \
    -v "$PROJECT_DIR":/home/user/Development:rw \
    -v "$ANDROID_SDK":"$CONTAINER_SDK":rw \
    -w /home/user/Development \
    -e ANDROID_HOME="$CONTAINER_SDK" \
    -e JAVA_HOME=/opt/java/openjdk \
    kivy/buildozer:latest \
    buildozer android debug 2>&1
