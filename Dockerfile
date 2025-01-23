FROM python:3.9-slim

# 安装ffmpeg
RUN apt-get update && apt-get install -y ffmpeg && rm -rf /var/lib/apt/lists/*

# 设置工作目录
WORKDIR /app

# 复制依赖文件
COPY requirements.txt .

# 安装依赖
RUN pip install --no-cache-dir -r requirements.txt

# 确保gunicorn已安装
RUN pip install gunicorn

# 复制应用代码
COPY . .

# 创建下载目录
RUN mkdir -p downloads && chmod 755 downloads

# 暴露端口
EXPOSE 8000

# 启动命令
CMD ["gunicorn", "--worker-class", "eventlet", "-w", "1", "--bind", "0.0.0.0:8000", "app:app"]
