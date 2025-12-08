#!/bin/bash

# Photo Upload App 打包脚本
# 使用 Docker 构建 Android APK

echo "========================================="
echo "Photo Upload App - APK 构建脚本"
echo "========================================="
echo ""

# 检查 Docker 是否安装
if ! command -v docker &> /dev/null; then
    echo "错误: Docker 未安装"
    echo "请先安装 Docker: https://docs.docker.com/get-docker/"
    exit 1
fi

echo "✓ Docker 已安装"
echo ""

# 检查 buildozer.spec 是否存在
if [ ! -f "buildozer.spec" ]; then
    echo "错误: 找不到 buildozer.spec 文件"
    echo "请确保在项目根目录运行此脚本"
    exit 1
fi

echo "✓ buildozer.spec 文件存在"
echo ""

echo "开始构建 APK..."
echo "这可能需要 30-60 分钟，请耐心等待..."
echo ""

# 使用 Docker 构建
docker run --rm -v "$(pwd)":/home/user/hostcwd kivy/buildozer android debug

# 检查构建结果
if [ $? -eq 0 ]; then
    echo ""
    echo "========================================="
    echo "✓ 构建成功！"
    echo "========================================="
    echo ""
    echo "APK 文件位置："
    ls -lh bin/*.apk 2>/dev/null || echo "未找到 APK 文件"
else
    echo ""
    echo "========================================="
    echo "✗ 构建失败"
    echo "========================================="
    echo ""
    echo "请检查上面的错误信息"
    exit 1
fi
