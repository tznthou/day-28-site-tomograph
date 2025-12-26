"""
Site Tomograph - 非同步爬蟲引擎
"""

import asyncio
import aiohttp
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from typing import AsyncGenerator, Set, Dict, List, Optional
from urllib.robotparser import RobotFileParser
import time
import random


class SiteCrawler:
    """
    非同步網站爬蟲，支援即時串流結果

    安全限制：
    - 最大頁面數：50 頁（防止無限爬取）
    - 請求間隔：500ms（降低伺服器負載）
    - 深度限制：預設 3 層
    - 並發限制：預設 3 個同時請求
    """

    def __init__(
        self,
        start_url: str,
        max_depth: int = 3,
        latency_threshold: int = 2000,  # 毫秒
        max_concurrent: int = 3,        # 降低並發數
        max_pages: int = 50,            # 總頁面上限
        request_delay: float = 0.5,     # 請求間隔（秒）
        max_retries: int = 3,           # 重試次數 (H06)
        respect_robots: bool = True     # 遵守 robots.txt (H04)
    ):
        self.start_url = start_url
        self.max_depth = max_depth
        self.latency_threshold = latency_threshold
        self.max_concurrent = max_concurrent
        self.max_pages = max_pages
        self.request_delay = request_delay
        self.max_retries = max_retries
        self.respect_robots = respect_robots

        # 解析起始 URL 的域名
        parsed = urlparse(start_url)
        self.base_domain = parsed.netloc
        self.base_scheme = parsed.scheme or "https"

        # 追蹤已訪問的 URL
        self.visited: Set[str] = set()

        # 儲存節點與連結資料
        self.nodes: Dict[str, dict] = {}
        self.links: List[dict] = []

        # 統計資料
        self.stats = {
            "total_pages": 0,
            "dead_links": 0,
            "slow_pages": 0,
            "orphan_pages": 0
        }

        # User-Agent 標明身份
        self.user_agent = "SiteTomograph/1.0 (Educational Tool; +https://github.com/tznthou/day-28-site-tomograph)"

        # robots.txt 解析器 (H04)
        self._robots_parser: Optional[RobotFileParser] = None
        self._robots_loaded = False

    def _normalize_url(self, url: str, base_url: str) -> str | None:
        """正規化 URL，只保留同域名的連結"""
        try:
            # 處理相對路徑
            full_url = urljoin(base_url, url)
            parsed = urlparse(full_url)

            # 只處理 http/https
            if parsed.scheme not in ("http", "https"):
                return None

            # 只處理同域名
            if parsed.netloc != self.base_domain:
                return None

            # 移除 fragment 和 query string（簡化）
            normalized = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"

            # 移除尾端斜線以統一
            if normalized.endswith("/") and len(parsed.path) > 1:
                normalized = normalized[:-1]

            return normalized
        except Exception:
            return None

    async def _load_robots_txt(self, session: aiohttp.ClientSession) -> None:
        """
        載入並解析 robots.txt (H04)
        """
        if self._robots_loaded:
            return

        self._robots_loaded = True
        robots_url = f"{self.base_scheme}://{self.base_domain}/robots.txt"

        try:
            async with session.get(
                robots_url,
                timeout=aiohttp.ClientTimeout(total=5),
                headers={"User-Agent": self.user_agent}
            ) as response:
                if response.status == 200:
                    content = await response.text()
                    self._robots_parser = RobotFileParser()
                    self._robots_parser.parse(content.splitlines())
        except Exception:
            # robots.txt 無法取得，預設允許所有
            pass

    def _can_fetch(self, url: str) -> bool:
        """
        檢查 robots.txt 是否允許爬取此 URL (H04)
        """
        if not self.respect_robots or self._robots_parser is None:
            return True

        return self._robots_parser.can_fetch(self.user_agent, url)

    async def _fetch_with_retry(
        self,
        session: aiohttp.ClientSession,
        url: str
    ) -> dict:
        """
        帶重試機制的頁面抓取 (H06)

        使用指數退避策略：
        - 第 1 次重試：等待 1-2 秒
        - 第 2 次重試：等待 2-4 秒
        - 第 3 次重試：等待 4-8 秒
        """
        last_error = None

        for attempt in range(self.max_retries):
            try:
                result = await self._fetch_page(session, url)

                # 如果是暫時性錯誤（5xx），重試
                if result["status_code"] in (500, 502, 503, 504) and attempt < self.max_retries - 1:
                    # 指數退避 + 隨機抖動
                    base_delay = 2 ** attempt
                    jitter = random.uniform(0, base_delay)
                    await asyncio.sleep(base_delay + jitter)
                    continue

                return result

            except Exception as e:
                last_error = e
                if attempt < self.max_retries - 1:
                    base_delay = 2 ** attempt
                    jitter = random.uniform(0, base_delay)
                    await asyncio.sleep(base_delay + jitter)

        # 所有重試都失敗
        return {
            "url": url,
            "status_code": 0,
            "latency": 0,
            "status": "necrosis",
            "links": [],
            "error": str(last_error) if last_error else "重試次數已達上限"
        }

    async def _fetch_page(
        self,
        session: aiohttp.ClientSession,
        url: str
    ) -> dict:
        """抓取單一頁面，回傳狀態與連結"""
        start_time = time.time()

        headers = {
            "User-Agent": self.user_agent,
            "Accept": "text/html,application/xhtml+xml",
        }

        try:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=10), headers=headers) as response:
                latency = int((time.time() - start_time) * 1000)
                status_code = response.status

                # 判斷狀態
                if status_code >= 400:
                    status = "necrosis"  # 壞死
                elif latency > self.latency_threshold:
                    status = "blockage"  # 阻塞
                else:
                    status = "healthy"   # 健康

                # 解析 HTML 抽取連結
                links = []
                if status_code == 200:
                    try:
                        html = await response.text()
                        soup = BeautifulSoup(html, "html.parser")

                        for a in soup.find_all("a", href=True):
                            link = self._normalize_url(a["href"], url)
                            if link and link != url:
                                links.append(link)
                    except Exception:
                        pass

                return {
                    "url": url,
                    "status_code": status_code,
                    "latency": latency,
                    "status": status,
                    "links": list(set(links))  # 去重
                }

        except asyncio.TimeoutError:
            latency = int((time.time() - start_time) * 1000)
            return {
                "url": url,
                "status_code": 408,  # Timeout
                "latency": latency,
                "status": "necrosis",
                "links": []
            }
        except Exception as e:
            return {
                "url": url,
                "status_code": 0,
                "latency": 0,
                "status": "necrosis",
                "links": [],
                "error": str(e)
            }

    async def scan(self) -> AsyncGenerator[dict, None]:
        """
        開始掃描，以 async generator 形式串流結果

        安全機制：
        - 達到 max_pages 上限時自動停止
        - 每個請求之間有 request_delay 間隔
        - 遵守 robots.txt 規則 (H04)
        - 失敗請求自動重試 (H06)
        """
        # 初始化佇列：(url, depth, parent_url)
        queue: List[tuple] = [(self.start_url, 0, None)]
        semaphore = asyncio.Semaphore(self.max_concurrent)

        async with aiohttp.ClientSession() as session:
            # 載入 robots.txt (H04)
            await self._load_robots_txt(session)

            while queue:
                # 安全檢查：達到頁面上限時停止
                if self.stats["total_pages"] >= self.max_pages:
                    yield {
                        "type": "limit_reached",
                        "message": f"已達到掃描上限（{self.max_pages} 頁），停止掃描以避免過度請求"
                    }
                    break

                # 取出下一個要處理的 URL
                current_url, depth, parent_url = queue.pop(0)

                # 跳過已訪問
                if current_url in self.visited:
                    continue

                # 檢查 robots.txt 是否允許 (H04)
                if not self._can_fetch(current_url):
                    continue

                self.visited.add(current_url)

                # 發現新節點事件
                node_id = f"node_{len(self.nodes)}"
                yield {
                    "type": "node_discovered",
                    "id": node_id,
                    "url": current_url,
                    "depth": depth
                }

                # 如果有父節點，建立連結
                if parent_url and parent_url in self.nodes:
                    parent_id = self.nodes[parent_url]["id"]
                    link_data = {
                        "source": parent_id,
                        "target": node_id
                    }
                    self.links.append(link_data)
                    yield {
                        "type": "link_discovered",
                        **link_data
                    }

                # 抓取頁面（帶重試機制）(H06)
                async with semaphore:
                    result = await self._fetch_with_retry(session, current_url)

                # 儲存節點資料
                self.nodes[current_url] = {
                    "id": node_id,
                    "depth": depth,
                    **result
                }

                # 更新統計
                self.stats["total_pages"] += 1
                if result["status"] == "necrosis":
                    self.stats["dead_links"] += 1
                elif result["status"] == "blockage":
                    self.stats["slow_pages"] += 1

                # 診斷更新事件
                yield {
                    "type": "diagnosis_update",
                    "id": node_id,
                    "url": current_url,
                    "status_code": result["status_code"],
                    "latency": result["latency"],
                    "status": result["status"]
                }

                # 如果未達最大深度，將子連結加入佇列
                if depth < self.max_depth:
                    for link in result["links"]:
                        if link not in self.visited:
                            queue.append((link, depth + 1, current_url))

                # 請求間隔：降低對目標伺服器的負載
                await asyncio.sleep(self.request_delay)

    def generate_report(self) -> dict:
        """產生診斷報告"""
        # 計算孤兒節點（in-degree = 0，除了起始節點）
        in_degree: Dict[str, int] = {node_id: 0 for node_id in [n["id"] for n in self.nodes.values()]}
        for link in self.links:
            if link["target"] in in_degree:
                in_degree[link["target"]] += 1

        orphans = []
        for url, node in self.nodes.items():
            if url != self.start_url and in_degree.get(node["id"], 0) == 0:
                orphans.append(url)
                self.stats["orphan_pages"] += 1

        # 建立完整頁面清單
        # 排序優先級：necrosis (0) → blockage (1) → healthy (2)
        # 同狀態內依 depth 淺到深
        status_priority = {"necrosis": 0, "blockage": 1, "healthy": 2}

        all_pages = []
        for url, node in self.nodes.items():
            all_pages.append({
                "url": url,
                "status": node["status"],
                "status_code": node["status_code"],
                "latency": node["latency"],
                "depth": node.get("depth", 0)
            })

        # 排序：狀態優先級 → 深度
        all_pages.sort(key=lambda x: (status_priority.get(x["status"], 2), x["depth"]))

        return {
            "summary": self.stats,
            "pages": all_pages,
            "orphan_nodes": orphans,
            "recommendations": self._generate_recommendations()
        }

    def _generate_recommendations(self) -> List[str]:
        """產生結構建議"""
        recommendations = []

        if self.stats["dead_links"] > 0:
            recommendations.append(
                f"發現 {self.stats['dead_links']} 個壞死連結，建議修復或移除"
            )

        if self.stats["slow_pages"] > 0:
            recommendations.append(
                f"發現 {self.stats['slow_pages']} 個高延遲頁面（> {self.latency_threshold}ms），建議優化"
            )

        if self.stats["orphan_pages"] > 0:
            recommendations.append(
                f"發現 {self.stats['orphan_pages']} 個孤兒頁面，建議建立內部連結"
            )

        if not recommendations:
            recommendations.append("網站結構健康，未發現明顯問題")

        return recommendations
