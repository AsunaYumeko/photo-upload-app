@echo off
echo ===================================
echo 提交所有项目文件到 Git
echo ===================================
echo.

echo 步骤 1: 添加所有文件...
git add .
if %errorlevel% neq 0 (
    echo 错误: 无法添加文件
    echo 请确保已安装 Git: https://git-scm.com/download/win
    pause
    exit /b 1
)

echo.
echo 步骤 2: 提交文件...
git commit -m "Add all project files including buildozer.spec"
if %errorlevel% neq 0 (
    echo 提示: 可能没有新的更改需要提交
)

echo.
echo 步骤 3: 推送到 GitHub...
git push origin main
if %errorlevel% neq 0 (
    echo 错误: 推送失败
    echo 请检查网络连接和 GitHub 认证
    pause
    exit /b 1
)

echo.
echo ===================================
echo 完成！文件已成功推送到 GitHub
echo ===================================
echo.
echo 现在可以访问 GitHub Actions 查看构建进度
echo https://github.com/AsunaYumeko/photo-upload-app/actions
echo.
pause
