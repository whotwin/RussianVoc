#!/bin/bash
set -e
export HOME=/home/hty
export JAVA_HOME=/home/hty/jdk/jdk-17.0.2
export PATH="$JAVA_HOME/bin:$HOME/.local/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
export ANDROID_HOME=/home/hty/android-sdk
export PATH="$PATH:$ANDROID_HOME/cmdline-tools/latest/bin:$ANDROID_HOME/platform-tools"
export PIP="$HOME/miniconda3/bin/pip"
export PYTHON="$HOME/miniconda3/bin/python3"
export DEBIAN_FRONTEND=noninteractive

cd /mnt/d/Development

echo "=== Java ==="
"$JAVA_HOME/bin/java" -version 2>&1 | head -1

echo "=== SDK Manager ==="
"$ANDROID_HOME/cmdline-tools/latest/bin/sdkmanager" --version

echo "=== Install system deps (requires sudo) ==="
sudo apt-get update -qq 2>&1 | tail -2
sudo apt-get install -y -qq zlib1g-dev python3-dev 2>&1 | tail -3

echo "=== Accept SDK licenses ==="
yes | "$ANDROID_HOME/cmdline-tools/latest/bin/sdkmanager" --licenses 2>&1 | grep -v '^$' | tail -5

echo "=== Build APK ==="
"$PYTHON" -m buildozer android debug 2>&1
echo "=== DONE ==="
