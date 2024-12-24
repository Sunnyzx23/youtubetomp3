# YouTube to MP3 Converter

一个简单的YouTube视频转MP3工具，使用Python和Flask实现。

## 功能特点

- 支持YouTube视频链接转换为MP3
- 实时显示下载进度
- 支持高质量音频转换
- 简洁的Web界面

## 安装要求

- Python 3.10+
- FFmpeg
- yt-dlp

## 依赖安装

```bash
pip install -r requirements.txt
```

## FFmpeg安装

### macOS
```bash
brew install ffmpeg
```

### Windows
1. 下载FFmpeg: https://ffmpeg.org/download.html
2. 解压并将ffmpeg.exe和ffprobe.exe放在项目根目录

### Linux
```bash
sudo apt-get install ffmpeg
```

## 使用方法

1. 克隆仓库
```bash
git clone https://github.com/Sunnyzx23/youtubetomp3.git
cd youtubetomp3
```

2. 安装依赖
```bash
pip install -r requirements.txt
```

3. 运行应用
```bash
python app.py
```

4. 打开浏览器访问 http://localhost:5004

## 注意事项

- 请确保有足够的磁盘空间
- 下载的文件会保存在downloads目录
- 需要稳定的网络连接
- 请遵守YouTube的服务条款

## 许可证

MIT License 