/**
 * Site Tomograph - 主入口
 */

class SiteTomograph {
    constructor() {
        // DOM 元素
        this.urlInput = document.getElementById('url-input');
        this.scanBtn = document.getElementById('scan-btn');
        this.stopBtn = document.getElementById('stop-btn');
        this.statusPanel = document.getElementById('status-panel');
        this.scanStatus = document.getElementById('scan-status');
        this.nodeCount = document.getElementById('node-count');
        this.deadCount = document.getElementById('dead-count');
        this.slowCount = document.getElementById('slow-count');
        this.nodeInfo = document.getElementById('node-info');
        this.infoContent = document.getElementById('info-content');
        this.reportPanel = document.getElementById('report-panel');
        this.reportContent = document.getElementById('report-content');
        this.loading = document.getElementById('loading');

        // 狀態
        this.ws = null;
        this.isScanning = false;
        this.stats = {
            total: 0,
            dead: 0,
            slow: 0
        };
        this.report = null;

        // 初始化 3D 圖
        this.graph = new SiteGraph(document.getElementById('graph-container'));
        this.graph.onNodeSelect = (node) => this.showNodeInfo(node);
        this.graph.onNodeHoverCallback = (node) => this.onNodeHover(node);

        // 綁定事件
        this.bindEvents();
    }

    bindEvents() {
        this.scanBtn.addEventListener('click', () => this.startScan());
        this.stopBtn.addEventListener('click', () => this.stopScan());

        this.urlInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                this.startScan();
            }
        });

        document.getElementById('download-report').addEventListener('click', () => {
            this.downloadReport();
        });

        document.getElementById('close-report').addEventListener('click', () => {
            this.reportPanel.classList.add('hidden');
        });
    }

    stopScan() {
        if (this.ws) {
            this.ws.close();
            this.ws = null;
        }
        this.scanStatus.textContent = '已手動停止';
        this.endScan();
    }

    startScan() {
        let url = this.urlInput.value.trim();

        if (!url) {
            alert('請輸入網址');
            return;
        }

        // 自動加上 https://
        if (!url.startsWith('http://') && !url.startsWith('https://')) {
            url = 'https://' + url;
        }

        // 驗證 URL
        try {
            new URL(url);
        } catch {
            alert('請輸入有效的網址');
            return;
        }

        // 重置狀態
        this.reset();
        this.isScanning = true;
        this.scanBtn.classList.add('hidden');
        this.stopBtn.classList.remove('hidden');
        this.statusPanel.classList.remove('hidden');
        this.scanStatus.textContent = '連接中...';
        this.loading.classList.remove('hidden');

        // 建立 WebSocket 連接
        const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        this.ws = new WebSocket(`${wsProtocol}//${window.location.host}/ws/scan`);

        this.ws.onopen = () => {
            this.scanStatus.textContent = '掃描中...';
            this.loading.classList.add('hidden');
            this.ws.send(JSON.stringify({ url }));
        };

        this.ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            this.handleMessage(data);
        };

        this.ws.onerror = (error) => {
            console.error('WebSocket error:', error);
            this.scanStatus.textContent = '連接錯誤';
            this.endScan();
        };

        this.ws.onclose = () => {
            if (this.isScanning) {
                this.endScan();
            }
        };
    }

    handleMessage(data) {
        switch (data.type) {
            case 'node_discovered':
                this.graph.addNode(data);
                this.stats.total++;
                this.nodeCount.textContent = this.stats.total;
                break;

            case 'link_discovered':
                this.graph.addLink(data);
                break;

            case 'diagnosis_update':
                this.graph.updateNodeDiagnosis(data);
                if (data.status === 'necrosis') {
                    this.stats.dead++;
                    this.deadCount.textContent = this.stats.dead;
                } else if (data.status === 'blockage') {
                    this.stats.slow++;
                    this.slowCount.textContent = this.stats.slow;
                }
                break;

            case 'scan_complete':
                this.report = data.report;
                this.showReport(data.report);
                this.endScan();
                break;

            case 'limit_reached':
                this.scanStatus.textContent = '已達上限';
                console.log(data.message);
                break;

            case 'error':
                alert(data.message);
                this.endScan();
                break;
        }
    }

    showNodeInfo(node) {
        this.nodeInfo.classList.remove('hidden');

        const statusText = {
            healthy: '健康',
            blockage: '阻塞',
            necrosis: '壞死',
            pending: '掃描中'
        };

        const statusClass = {
            healthy: 'style="color: #22c55e"',
            blockage: 'style="color: #d97706"',
            necrosis: 'style="color: #6b7280"',
            pending: ''
        };

        this.infoContent.innerHTML = `
            <div class="url">${this.escapeHtml(node.url)}</div>
            <div class="metric">
                <span>狀態</span>
                <span ${statusClass[node.status] || ''}>${statusText[node.status] || '-'}</span>
            </div>
            <div class="metric">
                <span>HTTP 狀態碼</span>
                <span>${node.statusCode || '-'}</span>
            </div>
            <div class="metric">
                <span>回應時間</span>
                <span>${node.latency ? node.latency + 'ms' : '-'}</span>
            </div>
            <div class="metric">
                <span>深度</span>
                <span>${node.depth}</span>
            </div>
        `;
    }

    onNodeHover(node) {
        if (node) {
            this.showNodeInfo(node);
        }
    }

    showReport(report) {
        this.reportPanel.classList.remove('hidden');

        let html = `
            <h3>摘要</h3>
            <div class="metric">
                <span>總頁面數</span>
                <span>${report.summary.total_pages}</span>
            </div>
            <div class="metric">
                <span>壞死連結</span>
                <span style="color: #6b7280">${report.summary.dead_links}</span>
            </div>
            <div class="metric">
                <span>高延遲頁面</span>
                <span style="color: #d97706">${report.summary.slow_pages}</span>
            </div>
            <div class="metric">
                <span>孤兒頁面</span>
                <span>${report.summary.orphan_pages}</span>
            </div>
        `;

        if (report.recommendations.length > 0) {
            html += '<h3 style="margin-top: 16px;">建議</h3><ul>';
            report.recommendations.forEach(rec => {
                html += `<li>${this.escapeHtml(rec)}</li>`;
            });
            html += '</ul>';
        }

        if (report.necrotic_tissue.length > 0) {
            html += '<h3 style="margin-top: 16px;">壞死組織</h3><ul>';
            report.necrotic_tissue.slice(0, 5).forEach(item => {
                html += `<li><code>${item.status_code}</code> ${this.escapeHtml(item.url)}</li>`;
            });
            if (report.necrotic_tissue.length > 5) {
                html += `<li>...還有 ${report.necrotic_tissue.length - 5} 個</li>`;
            }
            html += '</ul>';
        }

        this.reportContent.innerHTML = html;
    }

    downloadReport() {
        if (!this.report) return;

        const blob = new Blob([JSON.stringify(this.report, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'site-tomograph-report.json';
        a.click();
        URL.revokeObjectURL(url);
    }

    endScan() {
        this.isScanning = false;
        this.scanBtn.classList.remove('hidden');
        this.stopBtn.classList.add('hidden');
        this.loading.classList.add('hidden');

        if (this.ws) {
            this.ws.close();
            this.ws = null;
        }
    }

    reset() {
        this.graph.reset();
        this.stats = { total: 0, dead: 0, slow: 0 };
        this.nodeCount.textContent = '0';
        this.deadCount.textContent = '0';
        this.slowCount.textContent = '0';
        this.nodeInfo.classList.add('hidden');
        this.reportPanel.classList.add('hidden');
        this.report = null;
    }

    escapeHtml(str) {
        const div = document.createElement('div');
        div.textContent = str;
        return div.innerHTML;
    }
}

// 初始化
document.addEventListener('DOMContentLoaded', () => {
    window.app = new SiteTomograph();
});
