"""
Site Tomograph - 網站斷層掃描
FastAPI 後端入口
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from starlette.middleware.base import BaseHTTPMiddleware
from crawler import SiteCrawler
from security import (
    validate_url_safety,
    rate_limiter,
    ScanRequest,
    sanitize_error_message,
    SECURITY_HEADERS,
)
import json

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
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
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
async def index(request: Request):
    """主頁面"""
    return templates.TemplateResponse("index.html", {"request": request})


@app.websocket("/ws/scan")
async def websocket_scan(websocket: WebSocket):
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
            await websocket.send_json({"type": "error", "message": rate_error})
            return

        scan_started = True  # 標記已佔用速率限制槽位

        # ============================================================
        # 接收與驗證輸入 (H02)
        # ============================================================
        try:
            data = await websocket.receive_text()
            message = json.loads(data)
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
            await websocket.send_json({"type": "error", "message": safety_error})
            return

        # ============================================================
        # 執行掃描
        # ============================================================
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
        await websocket.send_json({
            "type": "scan_complete",
            "report": report
        })

    except WebSocketDisconnect:
        pass  # 客戶端斷線，靜默處理

    except Exception as e:
        # ============================================================
        # 安全錯誤處理 (H03)
        # ============================================================
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
