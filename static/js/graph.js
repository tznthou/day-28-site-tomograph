/**
 * Site Tomograph - 3D 力導向圖渲染
 */

class SiteGraph {
    constructor(container) {
        this.container = container;
        this.nodes = [];
        this.links = [];
        this.nodeMap = new Map();

        // 主題色彩定義
        this.themes = {
            dark: {
                bg: '#020205',
                healthy: '#00eeff',
                blockage: '#ff6600',
                necrosis: '#3a3a4a',
                link: 'rgba(0, 238, 255, 0.3)',
                particle: 'rgba(0, 238, 255, 0.8)'
            },
            light: {
                bg: '#f8f9fc',
                healthy: '#059669',
                blockage: '#d97706',
                necrosis: '#9ca3af',
                link: 'rgba(5, 150, 105, 0.3)',
                particle: 'rgba(5, 150, 105, 0.8)'
            }
        };

        this.init();
    }

    getTheme() {
        return document.documentElement.getAttribute('data-theme') === 'light' ? 'light' : 'dark';
    }

    getColors() {
        return this.themes[this.getTheme()];
    }

    init() {
        const colors = this.getColors();

        // 建立 3D 力導向圖
        this.graph = ForceGraph3D()(this.container)
            .backgroundColor(colors.bg)
            // 節點顏色：根據健康狀態 + 深度亮度
            .nodeColor(node => this.getNodeColor(node))
            .nodeOpacity(0.95)
            .nodeResolution(16)
            // 連線
            .linkColor(() => this.getColors().link)
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
            .linkDirectionalParticleColor(() => this.getColors().particle)
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
        const colors = this.getColors();
        const depth = Math.min(node.depth || 0, 3);

        // 根據健康狀態取得基礎色
        let baseColor;
        switch (node.status) {
            case 'necrosis':
                baseColor = colors.necrosis;
                break;
            case 'blockage':
                baseColor = colors.blockage;
                break;
            case 'healthy':
            default:
                baseColor = colors.healthy;
        }

        // 根據深度調整亮度
        // 深度 0 = 100%, 深度 1 = 75%, 深度 2 = 55%, 深度 3+ = 40%
        const brightness = [1.0, 0.75, 0.55, 0.4][depth];

        return this.adjustBrightness(baseColor, brightness);
    }

    // 調整顏色亮度
    adjustBrightness(hex, factor) {
        // 解析 hex 顏色
        const color = hex.replace('#', '');
        const r = parseInt(color.substring(0, 2), 16);
        const g = parseInt(color.substring(2, 4), 16);
        const b = parseInt(color.substring(4, 6), 16);

        // 調整亮度
        const newR = Math.round(r * factor);
        const newG = Math.round(g * factor);
        const newB = Math.round(b * factor);

        // 轉回 hex
        return '#' +
            newR.toString(16).padStart(2, '0') +
            newG.toString(16).padStart(2, '0') +
            newB.toString(16).padStart(2, '0');
    }

    // 更新主題色彩
    updateTheme() {
        const colors = this.getColors();
        this.graph.backgroundColor(colors.bg);
        // 重新渲染節點和連線顏色
        this.graph.nodeColor(node => this.getNodeColor(node));
        this.graph.linkColor(() => colors.link);
        this.graph.linkDirectionalParticleColor(() => colors.particle);
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

    /**
     * 完整清理 WebGL 資源 (H07)
     * 在元件銷毀時調用，避免記憶體洩漏
     */
    dispose() {
        // 清空資料
        this.nodes = [];
        this.links = [];
        this.nodeMap.clear();

        // 取得 Three.js 場景（如果可用）
        if (this.graph) {
            // 停止動畫循環
            this.graph.pauseAnimation();

            // 清理場景中的物件
            const scene = this.graph.scene();
            if (scene) {
                scene.traverse((object) => {
                    // 清理幾何體
                    if (object.geometry) {
                        object.geometry.dispose();
                    }
                    // 清理材質
                    if (object.material) {
                        if (Array.isArray(object.material)) {
                            object.material.forEach(material => {
                                this._disposeMaterial(material);
                            });
                        } else {
                            this._disposeMaterial(object.material);
                        }
                    }
                });

                // 清空場景
                while (scene.children.length > 0) {
                    scene.remove(scene.children[0]);
                }
            }

            // 清理渲染器
            const renderer = this.graph.renderer();
            if (renderer) {
                renderer.dispose();
                renderer.forceContextLoss();
                renderer.domElement = null;
            }

            // 清理控制器
            const controls = this.graph.controls();
            if (controls && controls.dispose) {
                controls.dispose();
            }
        }

        // 移除 DOM 元素中的 canvas
        while (this.container.firstChild) {
            this.container.removeChild(this.container.firstChild);
        }

        this.graph = null;
    }

    /**
     * 清理材質及其貼圖
     */
    _disposeMaterial(material) {
        if (!material) return;

        // 清理貼圖
        const textureProperties = [
            'map', 'alphaMap', 'aoMap', 'bumpMap', 'displacementMap',
            'emissiveMap', 'envMap', 'lightMap', 'metalnessMap',
            'normalMap', 'roughnessMap', 'specularMap'
        ];

        textureProperties.forEach(prop => {
            if (material[prop]) {
                material[prop].dispose();
            }
        });

        material.dispose();
    }
}

// 匯出
window.SiteGraph = SiteGraph;
