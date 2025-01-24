let currentTaskId = null;
const socket = io({
    path: '/socket.io',
    transports: ['websocket'],
    secure: true
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

// Event listeners
convertBtn.addEventListener('click', startConversion);
downloadBtn.addEventListener('click', downloadFile);

// WebSocket event handlers
socket.on('progress', handleProgress);
socket.on('complete', handleComplete);
socket.on('error', handleError);
socket.on('connect', () => {
    console.log('WebSocket connected');
});

socket.on('connect_error', (error) => {
    console.error('WebSocket connection error:', error);
    showError('Connection error, please refresh the page');
});

function startConversion() {
    const url = urlInput.value.trim();
    if (!url) {
        showError('Please enter a YouTube video URL');
        return;
    }
    
    // Reset UI
    resetUI();
    
    // Send conversion request
    fetch('/convert', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ url })
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            showError(data.error);
            return;
        }
        currentTaskId = data.task_id;
        progressDiv.style.display = 'block';
        convertBtn.disabled = true;
    })
    .catch(error => {
        showError('Server error, please try again later');
    });
}

function handleProgress(data) {
    if (data.task_id !== currentTaskId) return;
    
    progressBar.style.width = `${data.progress}%`;
    statusText.textContent = data.status === 'downloading' 
        ? `Downloading: ${Math.round(data.progress)}%`
        : 'Converting to MP3...';
}

function handleComplete(data) {
    if (data.task_id !== currentTaskId) return;
    
    progressBar.style.width = '100%';
    statusText.textContent = 'Conversion complete!';
    videoTitle.textContent = data.title;
    resultDiv.style.display = 'block';
}

function handleError(data) {
    if (data.task_id !== currentTaskId) return;
    showError(data.error);
    resetUI();
}

function downloadFile() {
    if (!currentTaskId) return;
    window.location.href = `/download/${currentTaskId}`;
}

function showError(message) {
    errorDiv.textContent = message;
    errorDiv.style.display = 'block';
}

function resetUI() {
    errorDiv.style.display = 'none';
    progressDiv.style.display = 'none';
    resultDiv.style.display = 'none';
    progressBar.style.width = '0%';
    statusText.textContent = 'Preparing to download...';
    convertBtn.disabled = false;
} 