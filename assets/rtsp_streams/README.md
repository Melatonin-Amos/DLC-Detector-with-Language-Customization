# RTSP 实时流配置说明

## 目录说明

本目录用于存放RTSP实时视频流的配置信息。

## 使用方法

### 1. 配置RTSP流地址

编辑 `stream_configs.json` 文件，添加您的摄像头RTSP地址：

```json
{
  "streams": [
    {
      "name": "living_room",
      "url": "rtsp://username:password@192.168.1.100:554/stream1",
      "resolution": "1080p",
      "fps": 25,
      "enabled": true
    }
  ]
}
```

### 2. 海康威视相机配置示例

海康威视相机的RTSP地址格式通常为：

```
rtsp://[username]:[password]@[IP地址]:[端口]/[路径]
```

**主码流**（高清）:
```
rtsp://admin:password@192.168.1.64:554/Streaming/Channels/101
```

**子码流**（标清，推荐用于测试）:
```
rtsp://admin:password@192.168.1.64:554/Streaming/Channels/102
```

### 3. 常见问题

**Q: 无法连接RTSP流？**
- 确保相机和电脑在同一局域网
- 检查用户名、密码是否正确
- 尝试使用VLC播放器测试RTSP地址是否可用
- 检查防火墙设置

**Q: 视频卡顿？**
- 使用子码流（较低分辨率）
- 检查网络带宽
- 调整关键帧提取间隔

### 4. 测试RTSP连接

使用项目提供的测试脚本：

```bash
python scripts/test_camera.py --source rtsp --url "rtsp://admin:password@192.168.1.64:554/Streaming/Channels/102"
```

## 注意事项

⚠️ **隐私提示**: 
- RTSP地址包含用户名和密码，请勿将 `stream_configs.json` 提交到Git
- 已在 `.gitignore` 中排除此文件
- 可以使用 `stream_configs.example.json` 作为模板
