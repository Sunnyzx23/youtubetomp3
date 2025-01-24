let currentTaskId = null;
let isConnected = false;

// 获取当前域名和协议
const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
const host = window.location.host;

// 创建Socket.IO实例
const socket = io({
    path: '/socket.io',
    transports: ['websocket', 'polling'],
    secure: true,
    reconnection: true,
    reconnectionAttempts: 5,
    reconnectionDelay: 1000,
    autoConnect: true,
    forceNew: true
});

// DOM elements
const urlInput = document.getElementById('url');
const convertBtn = document.getElementById('convert');
const progressDiv = document.getElementById('progress');
const progressBar = document.getElementById('progress-bar-fill');
const statusText = document.getElementById('status');
const errorDiv = document.getElementById('error');
const resultDiv = document.getElementById('result');
const videoTitle = document.getElementById('video-title');
const downloadBtn = document.getElementById('download');

// 初始化时禁用按钮
convertBtn.disabled = true;

// Event listeners
convertBtn.addEventListener('click', startConversion);
downloadBtn.addEventListener('click', downloadFile);

// WebSocket event handlers
socket.on('connect', () => {
    console.log('WebSocket connected successfully');
    isConnected = true;
    convertBtn.disabled = false;
    showStatus('Connected to server');
});

socket.on('disconnect', () => {
    console.log('WebSocket disconnected');
    isConnected = false;
    convertBtn.disabled = true;
    showError('Connection lost. Please refresh the page.');
});

socket.on('connect_error', (error) => {
    console.error('WebSocket connection error:', error);
    isConnected = false;
    convertBtn.disabled = true;
    showError('Connection error. Please refresh the page.');
});

socket.on('error', (error) => {
    console.error('Socket error:', error);
    showError('Server error occurred. Please try again.');
});

socket.on('progress', handleProgress);
socket.on('complete', handleComplete);

function startConversion() {
    if (!isConnected) {
        showError('Not connected to server. Please refresh the page.');
        return;
    }

    const url = urlInput.value.trim();
    if (!url) {
        showError('Please enter a YouTube video URL');
        return;
    }
    
    // Reset UI
    resetUI();
    showStatus('Starting conversion...');
    
    // Send conversion request
    fetch('/convert', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ url })
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Network response was not ok');
        }
        return response.json();
    })
    .then(data => {
        if (data.error) {
            showError(data.error);
            return;
        }
        currentTaskId = data.task_id;
        progressDiv.style.display = 'block';
        convertBtn.disabled = true;
        showStatus('Processing...');
    })
    .catch(error => {
        console.error('Conversion error:', error);
        showError('Server error, please try again later');
    });
}

function handleProgress(data) {
    console.log('Progress update:', data);
    if (data.task_id !== currentTaskId) return;
    
    progressBar.style.width = `${data.progress}%`;
    showStatus(data.status === 'downloading' 
        ? `Downloading: ${Math.round(data.progress)}%`
        : 'Converting to MP3...');
}

function handleComplete(data) {
    console.log('Conversion complete:', data);
    if (data.task_id !== currentTaskId) return;
    
    progressBar.style.width = '100%';
    showStatus('Conversion complete!');
    videoTitle.textContent = data.title;
    resultDiv.style.display = 'block';
}

function downloadFile() {
    if (!currentTaskId) return;
    showStatus('Starting download...');
    window.location.href = `/download/${currentTaskId}`;
}

function showError(message) {
    console.error('Error:', message);
    errorDiv.textContent = message;
    errorDiv.style.display = 'block';
    statusText.style.color = '#f87171';
}

function showStatus(message) {
    statusText.textContent = message;
    statusText.style.color = '';
}

function resetUI() {
    errorDiv.style.display = 'none';
    progressDiv.style.display = 'none';
    resultDiv.style.display = 'none';
    progressBar.style.width = '0%';
    showStatus('Preparing to download...');
    convertBtn.disabled = !isConnected;
} 