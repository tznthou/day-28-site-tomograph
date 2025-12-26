"""
Site Tomograph - 安全模組

提供 URL 驗證、SSRF 防護、速率限制等安全機制
"""

import ipaddress
import socket
from urllib.parse import urlparse
from typing import Tuple
from collections import defaultdict
import time
import asyncio


class SecurityError(Exception):
    """安全相關錯誤"""
    pass


# ============================================================
# SSRF 防護 (C01)
# ============================================================

# 危險域名黑名單
DANGEROUS_HOSTS = frozenset([
    "localhost",
    "127.0.0.1",
    "0.0.0.0",
    "::1",
    "[::1]",
    # AWS/GCP/Azure metadata endpoints
    "metadata.google.internal",
    "metadata.goog",
    "169.254.169.254",
    # Kubernetes
    "kubernetes.default.svc",
    # Docker
    "host.docker.internal",
])


def is_private_ip(ip_str: str) -> bool:
    """檢查是否為私有 IP 地址"""
    try:
        ip = ipaddress.ip_address(ip_str)
        return (
            ip.is_private or
            ip.is_loopback or
            ip.is_link_local or
            ip.is_multicast or
            ip.is_reserved or
            ip.is_unspecified
        )
    except ValueError:
        return False


def validate_url_safety(url: str) -> Tuple[bool, str]:
    """
    驗證 URL 安全性，防止 SSRF 攻擊

    Returns:
        Tuple[bool, str]: (是否安全, 錯誤訊息)
    """
    try:
        parsed = urlparse(url)
    except Exception:
        return False, "無效的 URL 格式"

    # 只允許 http/https
    if parsed.scheme not in ("http", "https"):
        return False, "只支援 HTTP/HTTPS 協定"

    # 取得主機名
    hostname = parsed.hostname
    if not hostname:
        return False, "缺少主機名"

    hostname_lower = hostname.lower()

    # 檢查危險域名黑名單
    if hostname_lower in DANGEROUS_HOSTS:
        return False, "不允許掃描此域名"

    # 檢查是否直接使用 IP
    try:
        ip = ipaddress.ip_address(hostname)
        if is_private_ip(hostname):
            return False, "不允許掃描私有 IP 位址"
    except ValueError:
        # 不是 IP，是域名，嘗試解析
        try:
            # 解析域名取得 IP
            resolved_ips = socket.getaddrinfo(hostname, None, socket.AF_UNSPEC, socket.SOCK_STREAM)
            for family, _, _, _, sockaddr in resolved_ips:
                ip_str = sockaddr[0]
                if is_private_ip(ip_str):
                    return False, "域名解析到私有 IP，不允許掃描"
        except socket.gaierror:
            return False, "無法解析域名"

    # 檢查 port（阻擋常見敏感 port）
    port = parsed.port
    if port:
        dangerous_ports = {22, 23, 25, 110, 143, 445, 3306, 5432, 6379, 27017}
        if port in dangerous_ports:
            return False, f"不允許掃描 port {port}"

    return True, ""


def sanitize_url_for_display(url: str) -> str:
    """清理 URL 以安全顯示（移除敏感資訊）"""
    try:
        parsed = urlparse(url)
        # 移除 userinfo
        safe_netloc = parsed.hostname or ""
        if parsed.port:
            safe_netloc += f":{parsed.port}"
        return f"{parsed.scheme}://{safe_netloc}{parsed.path}"
    except Exception:
        return "[無效 URL]"


# ============================================================
# 速率限制 (C02)
# ============================================================

class RateLimiter:
    """
    簡單的記憶體速率限制器

    限制：
    - 每個 IP 每分鐘最多 N 個請求
    - 全域最大並發掃描數
    """

    def __init__(
        self,
        requests_per_minute: int = 5,
        max_concurrent_scans: int = 10,
        cleanup_interval: int = 60
    ):
        self.requests_per_minute = requests_per_minute
        self.max_concurrent_scans = max_concurrent_scans
        self.cleanup_interval = cleanup_interval

        # IP -> [timestamp, ...]
        self._request_times: dict[str, list[float]] = defaultdict(list)
        # 目前進行中的掃描數
        self._active_scans = 0
        # 鎖
        self._lock = asyncio.Lock()
        # 上次清理時間
        self._last_cleanup = time.time()

    async def check_rate_limit(self, client_ip: str) -> Tuple[bool, str]:
        """
        檢查是否超過速率限制

        Returns:
            Tuple[bool, str]: (是否允許, 錯誤訊息)
        """
        async with self._lock:
            now = time.time()

            # 定期清理過期記錄
            if now - self._last_cleanup > self.cleanup_interval:
                self._cleanup_old_records(now)
                self._last_cleanup = now

            # 檢查全域並發限制
            if self._active_scans >= self.max_concurrent_scans:
                return False, "伺服器繁忙，請稍後再試"

            # 取得此 IP 的請求記錄
            request_times = self._request_times[client_ip]

            # 移除超過一分鐘的記錄
            cutoff = now - 60
            request_times[:] = [t for t in request_times if t > cutoff]

            # 檢查速率
            if len(request_times) >= self.requests_per_minute:
                return False, f"請求過於頻繁，請等待 {60 - int(now - request_times[0])} 秒後再試"

            # 記錄此次請求
            request_times.append(now)
            self._active_scans += 1

            return True, ""

    async def release_scan(self):
        """釋放一個掃描槽位"""
        async with self._lock:
            if self._active_scans > 0:
                self._active_scans -= 1

    def _cleanup_old_records(self, now: float):
        """清理過期記錄"""
        cutoff = now - 60
        empty_ips = []
        for ip, times in self._request_times.items():
            times[:] = [t for t in times if t > cutoff]
            if not times:
                empty_ips.append(ip)
        for ip in empty_ips:
            del self._request_times[ip]


# 全域速率限制器實例
rate_limiter = RateLimiter()


# ============================================================
# 輸入驗證 (H02)
# ============================================================

from pydantic import BaseModel, HttpUrl, field_validator


class ScanRequest(BaseModel):
    """掃描請求驗證模型"""
    url: str

    @field_validator('url')
    @classmethod
    def validate_url(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("URL 不可為空")

        # 自動補上 https://
        if not v.startswith(('http://', 'https://')):
            v = 'https://' + v

        # 長度限制
        if len(v) > 2048:
            raise ValueError("URL 過長")

        # 基本格式驗證
        try:
            parsed = urlparse(v)
            if not parsed.hostname:
                raise ValueError("無效的 URL 格式")
        except Exception:
            raise ValueError("無效的 URL 格式")

        return v


# ============================================================
# 錯誤處理 (H03)
# ============================================================

def sanitize_error_message(error: Exception) -> str:
    """
    清理錯誤訊息，移除敏感資訊

    避免洩漏：
    - 檔案路徑
    - 內部 IP
    - 堆疊追蹤
    - 系統資訊
    """
    error_str = str(error)

    # 常見的敏感模式
    sensitive_patterns = [
        ("/home/", ""),
        ("/var/", ""),
        ("/etc/", ""),
        ("/usr/", ""),
        ("192.168.", "[內部IP]"),
        ("10.", "[內部IP]"),
        ("172.16.", "[內部IP]"),
        ("127.0.0.1", "[localhost]"),
    ]

    for pattern, replacement in sensitive_patterns:
        if pattern in error_str:
            error_str = error_str.replace(pattern, replacement)

    # 如果錯誤訊息太長，截斷
    if len(error_str) > 200:
        error_str = error_str[:200] + "..."

    return error_str


# ============================================================
# 安全標頭 (C03)
# ============================================================

SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "X-XSS-Protection": "1; mode=block",
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "Content-Security-Policy": (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' https://unpkg.com; "
        "style-src 'self' 'unsafe-inline'; "
        "img-src 'self' data: blob:; "
        "connect-src 'self' ws: wss:; "
        "font-src 'self'; "
        "object-src 'none'; "
        "base-uri 'self';"
    ),
}
