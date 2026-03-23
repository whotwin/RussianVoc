#!/bin/bash
set -e
cd ~/android-sdk/cmdline-tools
echo "Files before: $(ls)"
if [ -f cmdline-tools.zip ]; then
    echo "Extracting..."
    python3 -c "import zipfile; zipfile.ZipFile('cmdline-tools.zip').extractall('.')"
    mv cmdline-tools latest 2>/dev/null || echo "mv failed"
    rm -f cmdline-tools.zip
fi
echo "Files after: $(ls)"
ls latest/bin/ 2>&1 | head -5
