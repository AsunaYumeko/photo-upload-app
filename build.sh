#!/bin/bash

# Photo Upload App 打包脚本
# 在 Linux 虚拟机中运行此脚本

echo "=== 安装 Docker ==="
sudo apt update
sudo apt install -y docker.io
sudo systemctl start docker
sudo systemctl enable docker

echo "=== 开始打包 APK ==="
sudo docker run --rm -v $(pwd):/home/user/hostcwd kivy/buildozer android debug

echo "=== 打包完成 ==="
echo "APK 文件在 bin/ 目录下"
ls -la bin/*.apk 2>/dev/null || echo "未找到 APK，请检查上面的错误信息"
