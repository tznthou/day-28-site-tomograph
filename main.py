"""
Site Tomograph - 網站斷層掃描
FastAPI 後端入口
"""

import asyncio
import logging
from datetime import datetime

from typing import Callable, Any

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response as StarletteResponse
from crawler import SiteCrawler
from security import (
    validate_url_safety,
    rate_limiter,
    ScanRequest,
    sanitize_error_message,
    SECURITY_HEADERS,
)
import json

# ============================================================
# 日誌設定 (M07)
# ============================================================

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger("site-tomograph")

app = FastAPI(
    title="Site Tomograph",
    description="3D 網站結構診斷儀",
    docs_url=None,  # 生產環境關閉 Swagger
    redoc_url=None,
)


# ============================================================
# 安全標頭中介層 (C03)
# ============================================================

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Any]
    ) -> StarletteResponse:
        response: StarletteResponse = await call_next(request)
        for header, value in SECURITY_HEADERS.items():
            response.headers[header] = value
        return response


app.add_middleware(SecurityHeadersMiddleware)


# ============================================================
# CORS 設定 (C03)
# ============================================================

# 生產環境應改為特定域名
ALLOWED_ORIGINS = [
    "http://localhost:8000",
    "http://127.0.0.1:8000",
    # 正式環境請加入實際域名
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


# 掛載靜態檔案
app.mount("/static", StaticFiles(directory="static"), name="static")

# 模板
templates = Jinja2Templates(directory="templates")


def get_client_ip(websocket: WebSocket) -> str:
    """取得客戶端 IP"""
    # 優先使用 X-Forwarded-For（若有反向代理）
    forwarded_for = websocket.headers.get("x-forwarded-for")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    # 否則使用直接連線 IP
    client = websocket.client
    return client.host if client else "unknown"


@app.get("/")
async def index(request: Request) -> Response:
    """主頁面"""
    return templates.TemplateResponse("index.html", {"request": request})


@app.websocket("/ws/scan")
async def websocket_scan(websocket: WebSocket) -> None:
    """WebSocket 端點：即時掃描串流"""
    await websocket.accept()

    client_ip = get_client_ip(websocket)
    scan_started = False

    try:
        # ============================================================
        # 速率限制檢查 (C02)
        # ============================================================
        allowed, rate_error = await rate_limiter.check_rate_limit(client_ip)
        if not allowed:
            logger.warning(f"[RATE_LIMIT] ip={client_ip} blocked")
            await websocket.send_json({"type": "error", "message": rate_error})
            return

        scan_started = True  # 標記已佔用速率限制槽位

        # ============================================================
        # 接收與驗證輸入 (H02, M02)
        # ============================================================
        # M02: 加入 30 秒接收逾時，防止閒置連線佔用資源
        try:
            data = await asyncio.wait_for(
                websocket.receive_text(),
                timeout=30.0
            )
            message = json.loads(data)
        except asyncio.TimeoutError:
            await websocket.send_json({"type": "error", "message": "連線逾時，請重新開始掃描"})
            return
        except json.JSONDecodeError:
            await websocket.send_json({"type": "error", "message": "無效的訊息格式"})
            return

        # Pydantic 驗證
        try:
            scan_request = ScanRequest(url=message.get("url", ""))
            start_url = scan_request.url
        except ValueError as e:
            await websocket.send_json({"type": "error", "message": str(e)})
            return

        # ============================================================
        # SSRF 防護 (C01)
        # ============================================================
        is_safe, safety_error = validate_url_safety(start_url)
        if not is_safe:
            logger.warning(f"[SSRF_BLOCK] ip={client_ip} url={start_url}")
            await websocket.send_json({"type": "error", "message": safety_error})
            return

        # ============================================================
        # 執行掃描
        # ============================================================
        logger.info(f"[SCAN_START] ip={client_ip} url={start_url}")
        scan_start_time = datetime.now()

        crawler = SiteCrawler(
            start_url=start_url,
            max_depth=3,
            latency_threshold=2000  # 2 秒
        )

        # 串流掃描結果
        async for event in crawler.scan():
            await websocket.send_json(event)

        # 掃描完成
        report = crawler.generate_report()
        scan_duration = (datetime.now() - scan_start_time).total_seconds()
        summary = report.get("summary", {})
        logger.info(
            f"[SCAN_COMPLETE] ip={client_ip} url={start_url} "
            f"pages={summary.get('total_pages', 0)} "
            f"dead={summary.get('dead_links', 0)} "
            f"slow={summary.get('slow_pages', 0)} "
            f"duration={scan_duration:.1f}s"
        )
        await websocket.send_json({
            "type": "scan_complete",
            "report": report
        })

    except WebSocketDisconnect:
        logger.info(f"[DISCONNECT] ip={client_ip} client disconnected")

    except Exception as e:
        # ============================================================
        # 安全錯誤處理 (H03)
        # ============================================================
        logger.error(f"[SCAN_ERROR] ip={client_ip} error={type(e).__name__}: {e}")
        safe_message = sanitize_error_message(e)
        try:
            await websocket.send_json({"type": "error", "message": safe_message})
        except Exception:
            pass  # 無法發送錯誤訊息，忽略

    finally:
        # 釋放速率限制槽位
        if scan_started:
            await rate_limiter.release_scan()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
