@echo off
wsl -d Ubuntu-22.04 bash /home/hty/wsl_build2.sh > /home/hty/build2.log 2>&1
echo EXIT:%ERRORLEVEL% >> /home/hty/build2.log
