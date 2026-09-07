// Global state
let currentVideoData = null;
let selectedFormatId = 'best';
let eventSource = null;

// DOM Elements
const urlInput = document.getElementById('video-url');
const btnParse = document.getElementById('btn-parse');
const parseSpinner = document.getElementById('parse-spinner');
const btnText = btnParse.querySelector('.btn-text');
const btnIcon = btnParse.querySelector('.btn-icon');
const errorMessage = document.getElementById('error-message');

const videoPanel = document.getElementById('video-panel');
const videoThumbnail = document.getElementById('video-thumbnail');
const videoDuration = document.getElementById('video-duration');
const videoTitle = document.getElementById('video-title');
const videoAuthor = document.getElementById('video-author-name');
const formatsList = document.getElementById('formats-list');
const btnDownload = document.getElementById('btn-download');

const progressPanel = document.getElementById('progress-panel');
const progressPercent = document.getElementById('progress-percent');
const progressBarFill = document.getElementById('progress-bar-fill');
const downloadStatusText = document.getElementById('download-status-text');
const downloadSpeed = document.getElementById('download-speed');
const downloadEta = document.getElementById('download-eta');

const filesList = document.getElementById('files-list');
const btnRefresh = document.getElementById('btn-refresh');
const notificationContainer = document.getElementById('notification-container');

// Initial Setup
document.addEventListener('DOMContentLoaded', () => {
    loadDownloadHistory();
    
    // Event Listeners
    btnParse.addEventListener('click', parseVideoUrl);
    urlInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            parseVideoUrl();
        }
    });
    
    btnDownload.addEventListener('click', startDownload);
    btnRefresh.addEventListener('click', loadDownloadHistory);
});

// Parse YouTube URL to fetch info
async function parseVideoUrl() {
    const url = urlInput.value.trim();
    if (!url) {
        showError('請輸入有效的影片網址！');
        return;
    }
    
    // Clear errors & hide panels
    hideError();
    videoPanel.classList.add('hidden');
    progressPanel.classList.add('hidden');
    
    // Show loading
    setParseLoading(true);
    
    try {
        const response = await fetch(`/api/info?url=${encodeURIComponent(url)}`);
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.detail || '分析影片失敗');
        }
        
        currentVideoData = data;
        renderVideoInfo(data);
        showNotification('影片分析成功！', 'success');
    } catch (err) {
        showError(err.message);
        showNotification(err.message, 'error');
    } finally {
        setParseLoading(false);
    }
}

// Render video metadata to the UI
function renderVideoInfo(data) {
    videoThumbnail.src = data.thumbnail;
    videoDuration.textContent = data.duration;
    videoTitle.textContent = data.title;
    videoAuthor.textContent = data.uploader;
    
    // Render formats list
    formatsList.innerHTML = '';
    
    // Selected format default
    selectedFormatId = 'best';
    
    data.formats.forEach((fmt) => {
        const option = document.createElement('div');
        option.className = `format-option ${fmt.id === 'best' ? 'selected' : ''}`;
        option.dataset.id = fmt.id;
        
        option.innerHTML = `
            <div class="format-res">${fmt.resolution}</div>
            <div class="format-note">${fmt.note || ''}</div>
        `;
        
        option.addEventListener('click', () => {
            document.querySelectorAll('.format-option').forEach(el => el.classList.remove('selected'));
            option.classList.add('selected');
            selectedFormatId = fmt.id;
        });
        
        formatsList.appendChild(option);
    });
    
    videoPanel.classList.remove('hidden');
    // Scroll to video panel
    videoPanel.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

// Start download process
async function startDownload() {
    if (!currentVideoData) return;
    
    const url = urlInput.value.trim();
    btnDownload.disabled = true;
    
    // Initialise progress UI
    updateProgressUI({
        percent: 0,
        status: 'downloading',
        speed: '0 B/s',
        eta: '計算中...'
    });
    progressPanel.classList.remove('hidden');
    progressPanel.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    
    try {
        const response = await fetch('/api/download', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ url: url, format_id: selectedFormatId })
        });
        
        const data = await response.json();
        if (!response.ok) {
            throw new Error(data.detail || '啟動下載失敗');
        }
        
        // Connect to progress event stream
        listenToProgress(data.download_id);
    } catch (err) {
        showNotification(err.message, 'error');
        btnDownload.disabled = false;
        progressPanel.classList.add('hidden');
    }
}

// Connect to SSE event stream
function listenToProgress(downloadId) {
    if (eventSource) {
        eventSource.close();
    }
    
    eventSource = new EventSource(`/api/progress/${downloadId}`);
    
    eventSource.onmessage = (event) => {
        const data = JSON.parse(event.data);
        
        if (data.status === 'downloading') {
            updateProgressUI({
                percent: data.percent,
                status: 'downloading',
                speed: data.speed,
                eta: data.eta
            });
        } else if (data.status === 'merging') {
            updateProgressUI({
                percent: 100,
                status: 'merging',
                speed: '0 B/s',
                eta: '處理中...'
            });
        } else if (data.status === 'complete') {
            eventSource.close();
            showNotification(`下載完成：${data.filename}`, 'success');
            progressPanel.classList.add('hidden');
            btnDownload.disabled = false;
            loadDownloadHistory();
        } else if (data.status === 'failed') {
            eventSource.close();
            showNotification(`下載失敗：${data.error}`, 'error');
            progressPanel.classList.add('hidden');
            btnDownload.disabled = false;
        }
    };
    
    eventSource.onerror = (err) => {
        console.error('EventSource error:', err);
        eventSource.close();
        showNotification('進度連線中斷，後端正在背景繼續下載。', 'error');
        btnDownload.disabled = false;
        progressPanel.classList.add('hidden');
        loadDownloadHistory(); // Reload in case it finishes
    };
}

// Update progress elements
function updateProgressUI({ percent, status, speed, eta }) {
    progressPercent.textContent = `${percent}%`;
    progressBarFill.style.width = `${percent}%`;
    
    if (status === 'downloading') {
        downloadStatusText.textContent = '正在下載中...';
    } else if (status === 'merging') {
        downloadStatusText.textContent = '正在進行影音合併/轉檔...';
    }
    
    downloadSpeed.textContent = speed;
    downloadEta.textContent = eta;
}

// Load download history list
async function loadDownloadHistory() {
    try {
        const response = await fetch('/api/files');
        const data = await response.json();
        
        renderHistoryList(data);
    } catch (err) {
        console.error('Error fetching files:', err);
        showNotification('載入歷史檔案失敗', 'error');
    }
}

// Render history to DOM
function renderHistoryList(files) {
    if (!files || files.length === 0) {
        filesList.innerHTML = `
            <div class="empty-history">
                <i class="fa-solid fa-folder-open empty-icon"></i>
                <p>目前沒有下載紀錄</p>
            </div>
        `;
        return;
    }
    
    filesList.innerHTML = '';
    files.forEach(file => {
        const isMp3 = file.filename.endsWith('.mp3');
        const iconClass = isMp3 ? 'fa-file-audio' : 'fa-file-video';
        
        const item = document.createElement('div');
        item.className = 'file-item';
        
        // Format creation time
        const date = new Date(file.created * 1000).toLocaleString('zh-TW', {
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
        
        item.innerHTML = `
            <div class="file-info">
                <i class="fa-solid ${iconClass} file-icon"></i>
                <div class="file-name-container">
                    <div class="file-name" title="${file.filename}">${file.filename}</div>
                    <div class="file-meta">${file.size} • ${date}</div>
                </div>
            </div>
            <div class="file-actions">
                <a href="/api/files/download/${encodeURIComponent(file.filename)}" download class="btn-action btn-download-file" title="儲存至本機">
                    <i class="fa-solid fa-download"></i> 保存
                </a>
                <button class="btn-action btn-delete-file" title="刪除檔案">
                    <i class="fa-solid fa-trash-can"></i> 刪除
                </button>
            </div>
        `;
        
        const deleteBtn = item.querySelector('.btn-delete-file');
        deleteBtn.addEventListener('click', () => deleteFile(file.filename));
        
        filesList.appendChild(item);
    });
}

// Delete file from history
async function deleteFile(filename) {
    if (!confirm(`確定要刪除此檔案嗎？\n${filename}`)) return;
    
    try {
        const response = await fetch(`/api/files/${encodeURIComponent(filename)}`, {
            method: 'DELETE'
        });
        const data = await response.json();
        
        if (response.ok && data.success) {
            showNotification('檔案已成功刪除', 'success');
            loadDownloadHistory();
        } else {
            throw new Error(data.detail || '刪除失敗');
        }
    } catch (err) {
        showNotification(err.message, 'error');
    }
}

// UI Helpers
function setParseLoading(isLoading) {
    if (isLoading) {
        btnParse.disabled = true;
        parseSpinner.style.display = 'inline-block';
        btnText.style.display = 'none';
        btnIcon.style.display = 'none';
    } else {
        btnParse.disabled = false;
        parseSpinner.style.display = 'none';
        btnText.style.display = 'inline-block';
        btnIcon.style.display = 'inline-block';
    }
}

function showError(msg) {
    errorMessage.textContent = msg;
    errorMessage.style.display = 'block';
}

function hideError() {
    errorMessage.textContent = '';
    errorMessage.style.display = 'none';
}

function showNotification(message, type = 'success') {
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    
    const icon = type === 'success' ? 'fa-circle-check' : 'fa-circle-exclamation';
    const iconColor = type === 'success' ? 'style="color: var(--accent-green)"' : 'style="color: var(--accent-red)"';
    
    notification.innerHTML = `
        <i class="fa-solid ${icon}" ${iconColor}></i>
        <div class="notification-text">${message}</div>
    `;
    
    notificationContainer.appendChild(notification);
    
    // Remove after 4s
    setTimeout(() => {
        notification.style.animation = 'fadeOut 0.3s ease-out forwards';
        setTimeout(() => {
            notification.remove();
        }, 300);
    }, 4000);
}
