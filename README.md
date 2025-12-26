# Site Tomograph 網站斷層掃描

[![License: AGPL-3.0](https://img.shields.io/badge/License-AGPL--3.0-blue.svg)](https://www.gnu.org/licenses/agpl-3.0)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688.svg)](https://fastapi.tiangolo.com/)
[![Three.js](https://img.shields.io/badge/Three.js-r158-000000.svg)](https://threejs.org/)
[![3d-force-graph](https://img.shields.io/badge/3d--force--graph-1.73-FF6B6B.svg)](https://github.com/vasturiano/3d-force-graph)
[![Tests](https://img.shields.io/badge/Tests-48%20passed-22c55e.svg)](tests/)

[← 回到 Muripo HQ](https://tznthou.github.io/muripo-hq/) | [English](README_EN.md)

一個低光度、高沈浸感的 3D 網站結構診斷儀。輸入網址後，觀看網站拓撲從中心點即時生長，透過視覺化的「衰敗機制」直覺發現死連結、慢速頁面與孤兒節點。

![Site Tomograph](assets/preview.webp)

> **"這不只是視覺作品，這是能讓開發者『看見』網站連結結構的專業診斷儀。"**

---

## 核心概念

傳統的網站健康檢查工具給你一份冰冷的報告。這個工具讓你**親眼看見**網站的神經網路如何生長、哪裡開始壞死。

透過低光度、高沈浸感的 3D 視覺化，打造一個讓開發者能安靜、舒適地觀察網站結構生長與衰亡的空間。

---

## 功能特色

| 功能 | 說明 |
|------|------|
| **即時拓撲生長** | 輸入網址後，看見網站結構從中心點非同步地向外擴散生長 |
| **延遲熱力映射** | 透過連線上的粒子流動速度，直覺呈現各頁面的回應延遲 |
| **死連結追蹤** | 點擊任何灰色壞死節點，高亮顯示所有指向該錯誤頁面的來源路徑 |
| **診斷報告匯出** | 掃描結束後，匯出包含「壞死組織清單」與「結構建議」的 JSON 報告 |
| **深色/淺色主題** | 支援雙主題切換，3D 圖表即時更新色彩配置 |

---

## 安全機制

本工具內建多層安全防護，確保負責任的網站掃描：

| 機制 | 說明 |
|------|------|
| **SSRF 防護** | 阻擋私有 IP、localhost、雲端 metadata endpoint 等危險目標 |
| **速率限制** | 每 IP 每分鐘最多 5 次請求，全域最大 10 個並發掃描 |
| **robots.txt 遵守** | 自動讀取並尊重目標網站的 robots.txt 規則 |
| **指數退避重試** | 對 5xx 錯誤自動重試，避免誤判暫時性故障 |
| **安全標頭** | 完整的 CSP、X-Frame-Options、X-Content-Type-Options 等 |
| **輸入驗證** | Pydantic 模型驗證 + 前端雙重檢查 |
| **錯誤遮蔽** | 錯誤訊息自動移除內部路徑、IP 等敏感資訊 |

---

## 視覺設計

### 色彩計畫

嚴格控制在低飽和度的冷靜色調，背景為純粹的深海黑，帶有極微弱的動態噪點：

| 狀態 | 色彩 | 說明 |
|------|------|------|
| **健康** | 磷光綠 `#22c55e` | 正常運作的頁面 |
| **阻塞** | 工業琥珀 `#d97706` | 回應時間 > 2 秒 |
| **壞死** | 死灰 `#6b7280` | HTTP 4xx/5xx 錯誤 |

### 衰敗機制

系統根據爬蟲結果，觸發溫和但明確的物理變化：

| 判定結果 | 閾值 | 視覺表現 |
|----------|------|----------|
| **數位壞疽** | HTTP 4xx/5xx | 節點轉為死灰色，像壞掉的燈泡般微弱閃爍，並緩緩下沉 |
| **黏滯阻塞** | Latency > 2000ms | 節點周圍產生半透明的琥珀色暈染，移動軌跡帶有沉重的拖影 |
| **光纖脈衝** | 正常 | 線條本身產生透明度的波動，模擬訊號在神經纖維中的安靜傳導 |
| **孤兒漂浮** | In-degree = 0 | 節點透明度降低，漂浮在邊緣，無連線接入 |

### 啟動美學

- **漸進浮現**：節點與連線緩緩浮現，無任何強烈閃爍，保護開發者長時間觀察的視覺舒適

---

## 技術架構

### 技術棧

| 技術 | 用途 | 備註 |
|------|------|------|
| [FastAPI](https://fastapi.tiangolo.com/) | 後端 API + WebSocket | 原生 WebSocket 支援 |
| [aiohttp](https://docs.aiohttp.org/) | 非同步爬蟲 | 高效能並發請求 |
| [BeautifulSoup4](https://www.crummy.com/software/BeautifulSoup/) | HTML 解析 | 連結抽取 |
| [3d-force-graph](https://github.com/vasturiano/3d-force-graph) | 3D 力導向圖 | 基於 Three.js |
| Vanilla JS | 無框架前端 | 模組化設計 |

### 爬蟲邏輯

```
┌─────────────────────────────────────────────────────────┐
│                    Crawling Engine                       │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  ┌──────────┐    ┌──────────────┐    ┌──────────────┐   │
│  │ 起始 URL │ →  │ DFS 深度優先 │ →  │ WebSocket    │   │
│  │          │    │ 最大 3 層    │    │ 即時串流     │   │
│  └──────────┘    └──────────────┘    └──────────────┘   │
│                                                          │
│  限制：同域名、並發控制、回應時間測量                    │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

### WebSocket 事件

| 事件 | 說明 |
|------|------|
| `node_discovered` | 發現新頁面，前端立即建立節點 |
| `link_discovered` | 發現頁面間的連結，前端建立連線 |
| `diagnosis_update` | 傳回該頁面的詳細診斷數據（狀態碼、回應時間） |
| `scan_complete` | 掃描完成，傳回完整報告 |

### 模組結構

| 模組 | 職責 |
|------|------|
| `main.py` | FastAPI 入口、WebSocket 端點、日誌記錄 |
| `crawler.py` | 非同步爬蟲引擎、robots.txt 遵守、重試機制 |
| `security.py` | SSRF 防護、速率限制、輸入驗證、安全標頭 |
| `static/js/graph.js` | 3D 力導向圖渲染、WebGL 資源管理 |
| `static/js/app.js` | 主入口、狀態管理、前端驗證 |
| `static/js/theme.js` | 深色/淺色主題切換 |
| `tests/` | 48 個單元測試（安全模組 + 爬蟲核心邏輯） |

---

## 判定邏輯

| 技術指標 | 判定閾值 | 系統觸發機制 |
|----------|----------|--------------|
| **HTTP 4xx/5xx** | 壞死 (Necrosis) | 節點變為灰色、停止脈動、產生下沉重力 |
| **Latency > 2000ms** | 阻塞 (Blockage) | 節點變為琥珀色、連線粒子流速變慢、產生黏滯感 |
| **In-degree = 0** | 孤兒 (Orphan) | 節點透明度降低、漂浮在邊緣、無連線接入 |
| **Out-degree > 50** | 資訊過載 (Overload) | 節點產生高頻震動、向四周噴發微小裝飾粒子 |

---

## 專案結構

```
day-28-site-tomograph/
├── main.py                    # FastAPI 入口、WebSocket、日誌
├── crawler.py                 # 非同步爬蟲引擎
├── security.py                # 安全模組（SSRF、速率限制、驗證）
├── templates/
│   └── index.html             # 主頁面
├── static/
│   ├── css/
│   │   └── style.css          # 深色/淺色主題樣式
│   └── js/
│       ├── graph.js           # 3D 力導向圖渲染
│       ├── theme.js           # 主題切換
│       └── app.js             # 主入口、狀態管理
├── tests/                     # 單元測試
│   ├── test_security.py       # 安全模組測試
│   └── test_crawler.py        # 爬蟲邏輯測試
├── assets/
│   └── preview.webp           # 預覽圖
├── pyproject.toml             # uv 專案設定
├── uv.lock                    # 依賴鎖定
├── LICENSE
├── README.md
└── README_EN.md
```

---

## 本地開發

```bash
# 複製專案
git clone https://github.com/tznthou/day-28-site-tomograph.git
cd day-28-site-tomograph

# 安裝依賴（使用 uv）
uv sync

# 啟動開發伺服器
uv run uvicorn main:app --reload

# 開啟瀏覽器
open http://localhost:8000
```

### 執行測試

```bash
# 安裝開發依賴
uv sync --extra dev

# 執行所有測試
uv run pytest tests/ -v

# 執行單一測試檔案
uv run pytest tests/test_security.py -v
```

---

## 部署

本專案部署於 [Zeabur](https://zeabur.com/)。

---

## 未來規劃

### 已完成 ✓
- [x] 深色/淺色主題切換
- [x] 完整安全機制（SSRF、速率限制、輸入驗證）
- [x] 單元測試覆蓋（48 個測試）
- [x] 結構化日誌記錄
- [x] robots.txt 遵守
- [x] 錯誤重試機制（指數退避）

### 視覺強化
- [ ] 自定義 Three.js Shader 實作「折射掃描面」效果
- [ ] 粒子系統優化，使用極低透明度疊加產生柔和發光感
- [ ] 音效設計：低頻環境嗡鳴聲 + 低通濾波處理

### 功能擴充
- [ ] 可配置的 Latency 閾值（UI 調整）
- [ ] 爬蟲深度可調整（1-5 層）
- [ ] 支援認證掃描（帶 Cookie/Token）
- [ ] SEO 指標整合（標題、描述、結構化資料）

---

## 隨想

### 一個簡單的需求

這個專案的核心功能其實很簡單：檢查網站的連結是否還活著、有沒有斷掉需要修復的地方。

但我想，既然要做，不如用一種有趣的方式來呈現。與其給出一份冰冷的清單，不如讓人「看見」網站的結構如何生長、哪裡開始衰敗。

### 意外的有趣

結果做出來的效果比預期有趣。看著節點一個一個冒出來，連線慢慢建立，壞掉的地方變灰下沉——這種「觀察」的過程本身就有一種奇妙的療癒感。

也許是因為平常我們只看到結果，很少有機會看到「過程」。

### 未來的可能

目前的版本只是個起點。腦中還有幾個想嘗試的方向：

- 加入音效，讓節點浮現時有微弱的聲響
- 更精緻的視覺特效，像真空管暖機般緩緩亮起
- 支援更多診斷指標，不只是連結健康度

有空再慢慢做。我想這會是一個蠻有趣的體驗。

---

## 授權

本作品採用 [AGPL-3.0](https://www.gnu.org/licenses/agpl-3.0) 授權。

這意味著：
- ✅ 可自由使用、修改、分發
- ✅ 可商業使用
- ⚠️ 修改後的版本必須開源
- ⚠️ 網路服務也必須提供原始碼

---

## 相關專案

- [Day-20 SEO Roaster](https://github.com/tznthou/day-20-seo-roaster) - SEO 吐槽器
- [Day-22 Site Portrait](https://github.com/tznthou/day-22-site-portrait) - 網站肖像海報
- [Day-23 City Breath](https://github.com/tznthou/day-23-city-breath) - 空氣品質視覺化

---

> **"看見結構，才能理解缺陷；理解缺陷，才能開始修復。"**
