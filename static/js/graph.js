/**
 * Site Tomograph - 3D 力導向圖渲染
 */

class SiteGraph {
    constructor(container) {
        this.container = container;
        this.nodes = [];
        this.links = [];
        this.nodeMap = new Map();

        // 色彩定義
        this.colors = {
            healthy: 0x22c55e,   // 磷光綠
            blockage: 0xd97706,  // 工業琥珀
            necrosis: 0x6b7280,  // 死灰
            link: 0x22c55e
        };

        this.init();
    }

    init() {
        // 建立 3D 力導向圖
        this.graph = ForceGraph3D()(this.container)
            .backgroundColor('#0a0a0f')
            .nodeColor(node => this.getNodeColor(node))
            .nodeOpacity(0.9)
            .nodeResolution(16)
            .linkColor(() => 'rgba(34, 197, 94, 0.3)')
            .linkOpacity(0.6)
            .linkWidth(1)
            .linkDirectionalParticles(2)
            .linkDirectionalParticleWidth(1.5)
            .linkDirectionalParticleSpeed(d => {
                // 根據目標節點的延遲調整粒子速度
                const targetNode = this.nodeMap.get(d.target);
                if (targetNode && targetNode.status === 'blockage') {
                    return 0.002; // 慢
                }
                return 0.008; // 正常
            })
            .linkDirectionalParticleColor(() => 'rgba(34, 197, 94, 0.8)')
            .onNodeClick(node => this.onNodeClick(node))
            .onNodeHover(node => this.onNodeHover(node));

        // 設定相機位置
        this.graph.cameraPosition({ x: 0, y: 0, z: 300 });

        // 真空管暖機效果
        this.container.style.opacity = '0';
        setTimeout(() => {
            this.container.style.transition = 'opacity 2s ease-out';
            this.container.style.opacity = '1';
        }, 100);
    }

    getNodeColor(node) {
        switch (node.status) {
            case 'necrosis':
                return '#6b7280';
            case 'blockage':
                return '#d97706';
            case 'healthy':
            default:
                return '#22c55e';
        }
    }

    addNode(nodeData) {
        const node = {
            id: nodeData.id,
            url: nodeData.url,
            depth: nodeData.depth,
            status: 'pending',
            statusCode: null,
            latency: null
        };

        this.nodes.push(node);
        this.nodeMap.set(nodeData.id, node);
        this.updateGraph();
    }

    addLink(linkData) {
        // 確保 source 和 target 都存在
        if (this.nodeMap.has(linkData.source) && this.nodeMap.has(linkData.target)) {
            this.links.push({
                source: linkData.source,
                target: linkData.target
            });
            this.updateGraph();
        }
    }

    updateNodeDiagnosis(data) {
        const node = this.nodeMap.get(data.id);
        if (node) {
            node.status = data.status;
            node.statusCode = data.status_code;
            node.latency = data.latency;
            this.updateGraph();
        }
    }

    updateGraph() {
        this.graph.graphData({
            nodes: this.nodes,
            links: this.links
        });
    }

    onNodeClick(node) {
        if (!node) return;

        // 聚焦到該節點
        const distance = 100;
        const distRatio = 1 + distance / Math.hypot(node.x, node.y, node.z);

        this.graph.cameraPosition(
            { x: node.x * distRatio, y: node.y * distRatio, z: node.z * distRatio },
            node,
            1000
        );

        // 觸發事件
        if (this.onNodeSelect) {
            this.onNodeSelect(node);
        }
    }

    onNodeHover(node) {
        this.container.style.cursor = node ? 'pointer' : 'default';

        if (this.onNodeHoverCallback) {
            this.onNodeHoverCallback(node);
        }
    }

    reset() {
        this.nodes = [];
        this.links = [];
        this.nodeMap.clear();
        this.updateGraph();
    }
}

// 匯出
window.SiteGraph = SiteGraph;
