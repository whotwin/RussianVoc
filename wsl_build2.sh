#!/bin/bash
set -e
export HOME=/home/hty
export JAVA_HOME=/home/hty/jdk/jdk-17.0.2
export PATH=$JAVA_HOME/bin:$HOME/.local/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
export ANDROID_HOME=/home/hty/android-sdk
export PATH=$PATH:$ANDROID_HOME/cmdline-tools/latest/bin:$ANDROID_HOME/platform-tools
export PIP=/home/hty/miniconda3/bin/pip
export DEBIAN_FRONTEND=noninteractive

cd /mnt/d/Development

echo "=== Java ==="
$JAVA_HOME/bin/java -version 2>&1 | head -1

echo "=== SDK Manager version ==="
sdkmanager --version

echo "=== Installing build deps ==="
sudo apt-get update -qq 2>&1 | tail -2
sudo apt-get install -y -qq zlib1g-dev python3-dev 2>&1 | tail -3

echo "=== Accepting SDK licenses ==="
yes | sdkmanager --licenses 2>&1 | grep -E "license|accepted|All" | tail -5 || true

echo "=== Installing buildozer ==="
$PIP install buildozer cython 2>&1 | tail -5

echo "=== Building APK ==="
buildozer android debug 2>&1
echo "=== BUILD_COMPLETE ==="
