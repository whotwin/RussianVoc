#!/bin/bash
ANDROID_SDK=/home/hty/android-sdk
PROJECT_DIR=/mnt/d/Development
CONTAINER_SDK=/root/.buildozer

# Run container with bash entrypoint, then run buildozer via python3
docker run --rm \
    --entrypoint /bin/bash \
    -i \
    -v "$PROJECT_DIR":/home/user/Development:rw \
    -v "$ANDROID_SDK":"$CONTAINER_SDK":rw \
    -w /home/user/Development \
    -e ANDROID_HOME="$CONTAINER_SDK" \
    -e JAVA_HOME=/opt/java/openjdk \
    kivy/buildozer:latest \
    -c "echo y | python3 /home/user/.venv/bin/buildozer android debug 2>&1"
