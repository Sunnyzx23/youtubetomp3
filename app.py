from flask import Flask, render_template, request, send_file, jsonify
from flask_socketio import SocketIO, emit
from flask_cors import CORS
import yt_dlp
import os
import uuid
from threading import Thread
import logging
import urllib.request
import zipfile
import shutil
import platform
import tempfile

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})
socketio = SocketIO(app, 
    cors_allowed_origins="*",
    async_mode='eventlet',
    logger=True,
    engineio_logger=True,
    ping_timeout=60,
    ping_interval=25,
    max_http_buffer_size=1e8,
    async_handlers=True
)

# 配置日志
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# 存储转换任务状态
conversion_tasks = {}

# 在文件顶部添加
WORKSPACE_PATH = os.path.abspath(os.path.dirname(__file__))
FFMPEG_DIR = WORKSPACE_PATH  # ffmpeg和ffprobe所在的目录
FFMPEG_PATH = os.path.join(FFMPEG_DIR, 'ffmpeg')
FFPROBE_PATH = os.path.join(FFMPEG_DIR, 'ffprobe')

print(f"Workspace Path: {WORKSPACE_PATH}")
print(f"FFmpeg Path: {FFMPEG_PATH}")
print(f"FFprobe Path: {FFPROBE_PATH}")

def check_ffmpeg():
    """检查ffmpeg是否正确安装并支持mp3编码"""
    try:
        # 检查ffmpeg版本
        result = os.popen(f"{FFMPEG_PATH} -version").read()
        print(f"FFmpeg version info:\n{result}")
        
        # 检查mp3编码器支持
        result = os.popen(f"{FFMPEG_PATH} -codecs | grep mp3").read()
        print(f"FFmpeg MP3 codec support:\n{result}")
        
        return True
    except Exception as e:
        print(f"FFmpeg check failed: {str(e)}")
        return False

# 检查ffmpeg和ffprobe
for path in [FFMPEG_PATH, FFPROBE_PATH]:
    if os.path.exists(path):
        os.chmod(path, 0o755)
        print(f"File exists and permissions set for: {path}")
    else:
        print(f"WARNING: File not found: {path}")

# 在启动时检查ffmpeg
if not check_ffmpeg():
    print("WARNING: FFmpeg check failed, audio conversion may not work properly")

class ProgressHook:
    def __init__(self, task_id):
        self.task_id = task_id
    
    def __call__(self, d):
        if d['status'] == 'downloading':
            progress = (d.get('downloaded_bytes', 0) / d.get('total_bytes', 1)) * 100
            socketio.emit('progress', {
                'task_id': self.task_id,
                'progress': progress,
                'status': 'downloading'
            })
        elif d['status'] == 'finished':
            socketio.emit('progress', {
                'task_id': self.task_id,
                'progress': 100,
                'status': 'completed'  # 直接完成，不需要转换
            })

def convert_to_mp3(input_file, output_file):
    """使用ffmpeg直接转换文件为MP3格式"""
    try:
        cmd = f'{FFMPEG_PATH} -i "{input_file}" -vn -acodec libmp3lame -q:a 2 "{output_file}"'
        print(f"Running conversion command: {cmd}")
        result = os.system(cmd)
        if result != 0:
            raise Exception(f"FFmpeg conversion failed with exit code {result}")
        return True
    except Exception as e:
        print(f"Conversion error: {str(e)}")
        return False

def download_and_convert(url, task_id):
    try:
        output_dir = 'downloads'
        task_dir = os.path.join(output_dir, task_id)
        if not os.path.exists(task_dir):
            os.makedirs(task_dir)
            
        # 第一步：只下载音频，不做转换
        ydl_opts = {
            'format': 'bestaudio/best',
            'ffmpeg_location': FFMPEG_DIR,
            'prefer_ffmpeg': True,
            'progress_hooks': [ProgressHook(task_id)],
            'outtmpl': f'{task_dir}/%(title)s.%(ext)s',
            'nocheckcertificate': True,
            'verbose': True,
            'logtostderr': True
        }
        
        # 打印调试信息
        print(f"Current working directory: {os.getcwd()}")
        print(f"Task directory: {task_dir}")
        print(f"FFmpeg exists: {os.path.exists(FFMPEG_PATH)}")
        print(f"FFprobe exists: {os.path.exists(FFPROBE_PATH)}")
        
        # 确保ffmpeg可执行
        os.chmod(FFMPEG_PATH, 0o755)
        os.chmod(FFPROBE_PATH, 0o755)
        
        # 下载文件
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            print("Starting download with yt-dlp...")
            info = ydl.extract_info(url, download=True)
            title = info['title']
            
        # 找到下载的音频文件
        downloaded_file = None
        for file in os.listdir(task_dir):
            if os.path.isfile(os.path.join(task_dir, file)):
                downloaded_file = os.path.join(task_dir, file)
                break
                
        if not downloaded_file:
            raise Exception('Download failed: No file found')
            
        # 第二步：手动转换为MP3
        output_file = os.path.join(task_dir, f"{title}.mp3")
        print(f"Converting {downloaded_file} to {output_file}")
        
        if not convert_to_mp3(downloaded_file, output_file):
            raise Exception('Conversion to MP3 failed')
            
        # 删除原始文件
        if os.path.exists(downloaded_file) and downloaded_file != output_file:
            os.remove(downloaded_file)
                
        conversion_tasks[task_id] = {
            'status': 'completed',
            'file_path': output_file,
            'title': title,
            'ext': 'mp3'
        }
        
        socketio.emit('complete', {
            'task_id': task_id,
            'title': title
        })
        
    except Exception as e:
        logger.error(f"Error processing {url}: {str(e)}")
        error_message = str(e)
        if 'certificate verify failed' in error_message:
            error_message = 'Network connection error, please try again'
        elif 'Video unavailable' in error_message:
            error_message = 'Video is unavailable or has been deleted'
        elif 'Private video' in error_message:
            error_message = 'This video is private and cannot be accessed'
        conversion_tasks[task_id] = {
            'status': 'error',
            'error': error_message
        }
        socketio.emit('error', {
            'task_id': task_id,
            'error': error_message
        })

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/convert', methods=['POST'])
def convert():
    url = request.json.get('url')
    if not url:
        return jsonify({'error': 'Please enter a YouTube video URL'}), 400
        
    # 验证URL格式
    if not url.startswith(('https://www.youtube.com/', 'https://youtu.be/')):
        return jsonify({'error': 'Please enter a valid YouTube video URL'}), 400
        
    task_id = str(uuid.uuid4())
    conversion_tasks[task_id] = {'status': 'processing'}
    
    Thread(target=download_and_convert, args=(url, task_id)).start()
    
    return jsonify({'task_id': task_id})

@app.route('/download/<task_id>')
def download(task_id):
    task = conversion_tasks.get(task_id)
    if not task or task.get('status') != 'completed':
        return jsonify({'error': 'File not found or conversion not completed'}), 404
        
    return send_file(
        task['file_path'],
        as_attachment=True,
        download_name=f"{task['title']}.{task['ext']}"
    )

if __name__ == '__main__':
    socketio.run(app, debug=True, port=5004) 