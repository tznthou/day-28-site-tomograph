"""
Site Tomograph - 非同步爬蟲引擎
"""

import asyncio
import aiohttp
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from typing import AsyncGenerator, Set, Dict, List
import time


class SiteCrawler:
    """非同步網站爬蟲，支援即時串流結果"""

    def __init__(
        self,
        start_url: str,
        max_depth: int = 3,
        latency_threshold: int = 2000,  # 毫秒
        max_concurrent: int = 5
    ):
        self.start_url = start_url
        self.max_depth = max_depth
        self.latency_threshold = latency_threshold
        self.max_concurrent = max_concurrent

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

    async def _fetch_page(
        self,
        session: aiohttp.ClientSession,
        url: str
    ) -> dict:
        """抓取單一頁面，回傳狀態與連結"""
        start_time = time.time()

        try:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as response:
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
        """
        # 初始化佇列：(url, depth, parent_url)
        queue: List[tuple] = [(self.start_url, 0, None)]
        semaphore = asyncio.Semaphore(self.max_concurrent)

        async with aiohttp.ClientSession() as session:
            while queue:
                # 取出下一個要處理的 URL
                current_url, depth, parent_url = queue.pop(0)

                # 跳過已訪問
                if current_url in self.visited:
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

                # 抓取頁面
                async with semaphore:
                    result = await self._fetch_page(session, current_url)

                # 儲存節點資料
                self.nodes[current_url] = {
                    "id": node_id,
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

                # 避免過快發送訊息
                await asyncio.sleep(0.1)

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

        # 壞死清單
        necrotic_list = [
            {"url": url, "status_code": node["status_code"]}
            for url, node in self.nodes.items()
            if node["status"] == "necrosis"
        ]

        # 阻塞清單
        blocked_list = [
            {"url": url, "latency": node["latency"]}
            for url, node in self.nodes.items()
            if node["status"] == "blockage"
        ]

        return {
            "summary": self.stats,
            "necrotic_tissue": necrotic_list,
            "blocked_arteries": blocked_list,
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
