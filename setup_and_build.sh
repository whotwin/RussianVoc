#!/bin/bash
set -e
export JAVA_HOME=/home/hty/jdk/jdk-17.0.2
export PATH=$JAVA_HOME/bin:$HOME/.local/bin:$PATH
export ANDROID_HOME=/home/hty/android-sdk
export PATH=$PATH:$ANDROID_HOME/cmdline-tools/latest/bin:$ANDROID_HOME/platform-tools

echo "=== Java ==="
java -version 2>&1 | head -1

echo "=== Accepting SDK licenses ==="
yes | $ANDROID_HOME/cmdline-tools/latest/bin/sdkmanager --licenses > /dev/null 2>&1 || true

echo "=== Installing SDK components ==="
$ANDROID_HOME/cmdline-tools/latest/bin/sdkmanager 'platform-tools' 'platforms;android-34' 'build-tools;34.0.0' 2>&1
echo "SDK OK"

echo "=== Installing buildozer ==="
pip3 install buildozer 2>&1 | tail -5

echo "=== Installing buildozer deps ==="
pip3 install cython 2>&1 | tail -3

echo "=== Building APK ==="
cd /mnt/d/Development
buildozer android debug 2>&1
echo "BUILD_DONE"
