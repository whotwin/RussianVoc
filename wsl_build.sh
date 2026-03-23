#!/bin/bash
set -e
export DEBIAN_FRONTEND=noninteractive

echo "=== Installing Java 17 ==="
sudo apt-get update -qq
sudo apt-get install -y -qq openjdk-17-jdk wget unzip > /dev/null 2>&1
echo "Java installed:"
java -version 2>&1 | head -1

echo "=== Installing Android SDK ==="
mkdir -p ~/android-sdk/cmdline-tools
cd ~/android-sdk/cmdline-tools
if [ ! -d latest ]; then
    wget -q https://dl.google.com/android/repository/commandlinetools-linux-11076708_latest.zip -O cmdline-tools.zip
    unzip -q cmdline-tools.zip
    mv cmdline-tools latest
    rm cmdline-tools.zip
fi
export ANDROID_HOME=$HOME/android-sdk
export PATH=$PATH:$ANDROID_HOME/cmdline-tools/latest/bin:$ANDROID_HOME/platform-tools
echo "Accepting SDK licenses..."
yes | sdkmanager --licenses > /dev/null 2>&1 || true
echo "Installing SDK components..."
sdkmanager 'platform-tools' 'platforms;android-34' 'build-tools;34.0.0' > /dev/null 2>&1
echo "SDK installed at $ANDROID_HOME"

echo "=== Installing buildozer ==="
cd /mnt/d/Development
pip install buildozer 2>&1 | tail -3

echo "=== Building APK ==="
export ANDROID_HOME=$HOME/android-sdk
export PATH=$PATH:$ANDROID_HOME/cmdline-tools/latest/bin:$ANDROID_HOME/platform-tools
buildozer android debug 2>&1
