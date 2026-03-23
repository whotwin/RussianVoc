#!/bin/bash
set -e
ANDROID_SDK=/home/hty/android-sdk
JDK_DIR=/home/hty/jdk
PROJECT_DIR=/mnt/d/Development
CONTAINER_SDK=/root/.buildozer
CONTAINER_JDK=/root/jdk

# Patch buildozer root check then build, piping y to all prompts
docker run --rm \
    --entrypoint /bin/bash \
    -i \
    -v "$PROJECT_DIR":/home/user/Development:rw \
    -v "$ANDROID_SDK":"$CONTAINER_SDK":rw \
    -v "$JDK_DIR":"$CONTAINER_JDK":rw \
    -w /home/user/Development \
    -e ANDROID_HOME="$CONTAINER_SDK" \
    -e JAVA_HOME="$CONTAINER_JDK/jdk-17.0.2" \
    kivy/buildozer:latest \
    -c "python3 -c \"import site,os; p=os.path.join(site.getsitepackages()[0],'buildozer/__init__.py'); c=open(p).read().replace('self.check_root()','pass'); open(p,'w').write(c)\" && yes y | python3 /home/user/.venv/bin/buildozer android debug"
