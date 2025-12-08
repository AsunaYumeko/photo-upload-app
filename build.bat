@echo off
REM Photo Upload App 打包脚本 (Windows)
REM 使用 Docker 构建 Android APK

echo =========================================
echo Photo Upload App - APK 构建脚本
echo =========================================
echo.

REM 检查 Docker 是否安装
docker --version >nul 2>&1
if %errorlevel% neq 0 (
    echo 错误: Docker 未安装
    echo 请先安装 Docker Desktop: https://www.docker.com/products/docker-desktop
    pause
    exit /b 1
)

echo √ Docker 已安装
echo.

REM 检查 buildozer.spec 是否存在
if not exist "buildozer.spec" (
    echo 错误: 找不到 buildozer.spec 文件
    echo 请确保在项目根目录运行此脚本
    pause
    exit /b 1
)

echo √ buildozer.spec 文件存在
echo.

echo 开始构建 APK...
echo 这可能需要 30-60 分钟，请耐心等待...
echo.

REM 使用 Docker 构建
docker run --rm -v "%cd%":/home/user/hostcwd kivy/buildozer android debug

if %errorlevel% equ 0 (
    echo.
    echo =========================================
    echo √ 构建成功！
    echo =========================================
    echo.
    echo APK 文件位置：
    dir /b bin\*.apk 2>nul || echo 未找到 APK 文件
) else (
    echo.
    echo =========================================
    echo × 构建失败
    echo =========================================
    echo.
    echo 请检查上面的错误信息
)

echo.
pause
