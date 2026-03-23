#!/bin/bash
set -e
export DEBIAN_FRONTEND=noninteractive
export JAVA_HOME=/home/hty/jdk/jdk-17.0.2
export PATH=$JAVA_HOME/bin:$HOME/.local/bin:$PATH
export ANDROID_HOME=/home/hty/android-sdk
export PATH=$PATH:$ANDROID_HOME/cmdline-tools/latest/bin:$ANDROID_HOME/platform-tools
export PIP=/home/hty/miniconda3/bin/pip

echo "=== Java ==="
$JAVA_HOME/bin/java -version 2>&1 | head -1

echo "=== Installing build deps ==="
sudo apt-get update -qq 2>&1 | tail -3
sudo apt-get install -y zlib1g-dev python3-dev 2>&1 | tail -5 || echo "apt install failed, continuing..."

echo "=== Accepting SDK licenses ==="
yes | $ANDROID_HOME/cmdline-tools/latest/bin/sdkmanager --licenses 2>&1 | grep -v '^$' || true

echo "=== Installing SDK platform-tools + platform-34 + build-tools ==="
$ANDROID_HOME/cmdline-tools/latest/bin/sdkmanager 'platform-tools' 'platforms;android-34' 'build-tools;34.0.0' 2>&1
echo "SDK installed"

echo "=== Installing buildozer ==="
$PIP install buildozer 2>&1 | tail -5
$PIP install cython 2>&1 | tail -3

echo "=== Building APK ==="
cd /mnt/d/Development
buildozer android debug 2>&1
echo "=== BUILD_COMPLETE ==="
