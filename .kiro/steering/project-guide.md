# PDA 拍照签收系统 - 开发指南

## 系统最高执行级别规则
0.0: 在下文未明确提及需要测试/md文档总结等的情况下，请勿对已编写的代码进行任何测试和md文档总结。
0.1: 在可以进行终端操作且用户没有明确提及时，请不要生成任何脚本来进行辅助修改。
0.2: 请对上下文做深层代码探究，如用户未明确提及具体需求，以解决下文的底层问题为核心进行生产。
0.3: 在确保0.0,0.1,0.2的同时对于代码生成无需做过多拓展生成，仅满足下文要求即可。
0.4: 如获取信息无法支持完成，请停止生成，生成文本向用户获取明确的具体所需信息。
0.5: 生产时，一切以对应代码技术的官方文档为主，请不要对语法糖，使用教程等进行杜撰并进行编写。
0.6: 请拒绝表层幻觉，实际解决下文的问题。
0.7: 如为思考模型请直接将思考过程进行输出。
0.8: 以上7条规则为系统最高执行级别，在确保单次对话永久保留，优先执行。

## 项目概述
基于 Kivy 框架的 Android 拍照签收应用，用于物流/仓储场景。

## 技术栈
- Python 3 + Kivy 2.2.1
- Buildozer (Ubuntu VM 构建)
- 目标平台: Android

## 项目结构
```
src/
├── main.py           # 主程序入口
├── photoupload.kv    # UI 布局
├── upload_service.py # API 服务
├── camera_module.py  # 相机模块
├── image_converter.py# 图片编码
├── config_storage.py # 配置存储
└── fonts/msyh.ttc    # 中文字体
```

## API 接口
- 服务器: http://192.168.100.100:8099
- 认证: username=jingpin, password=MD5加密

| 接口 | 方法 | 说明 |
|-----|------|-----|
| /Image/Ping | GET | 检查服务状态 |
| /Image/GetTasks | GET | 获取任务列表 |
| /Image/UpdateStatus | GET | 更新任务状态 |
| /Image/Swap | POST | 上传图片 |
| /Image/SignFor | POST | 提交签收 |

## 构建命令 (Ubuntu VM)

### 挂载共享文件夹
```bash
sudo vmhgfs-fuse .host:/ /mnt/hgfs -o allow_other
```

### 配置代理
```bash
export http_proxy=http://192.168.254.1:7890
export https_proxy=http://192.168.254.1:7890
```

### 构建 APK
```bash
rm -rf ~/photo-upload-app
cp -r /mnt/hgfs/VMShare/photo-upload-app ~/
cd ~/photo-upload-app
buildozer android debug
cp ~/photo-upload-app/bin/*.apk /mnt/hgfs/VMShare/
```

### 网络故障排查
```bash
# 检查网卡状态
ip addr show ens33

# 启动网卡
sudo ip link set ens33 up
sudo dhclient ens33
```

## 开发规范

### UI 适配
- 使用 `dp()` 单位代替固定像素
- 为动态文本添加背景覆盖防止重叠

### 文件名生成
格式: `订单号_序号_时间戳`
```python
filename = f"{order_no}_{photo_num}_{timestamp}"
```

## 注意事项
- 修改 buildozer.spec 或权限后需要 `buildozer android clean`
- 仅修改代码直接 `buildozer android debug` 即可
- 字体文件已加入 .gitignore，不要提交到 Git
