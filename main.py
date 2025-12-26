"""
Site Tomograph - 網站斷層掃描
FastAPI 後端入口
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.requests import Request
from crawler import SiteCrawler
import json

app = FastAPI(title="Site Tomograph", description="3D 網站結構診斷儀")

# 掛載靜態檔案
app.mount("/static", StaticFiles(directory="static"), name="static")

# 模板
templates = Jinja2Templates(directory="templates")


@app.get("/")
async def index(request: Request):
    """主頁面"""
    return templates.TemplateResponse("index.html", {"request": request})


@app.websocket("/ws/scan")
async def websocket_scan(websocket: WebSocket):
    """WebSocket 端點：即時掃描串流"""
    await websocket.accept()

    try:
        # 接收起始 URL
        data = await websocket.receive_text()
        message = json.loads(data)
        start_url = message.get("url", "")

        if not start_url:
            await websocket.send_json({"type": "error", "message": "請提供有效的 URL"})
            return

        # 建立爬蟲並開始掃描
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
        print("Client disconnected")
    except Exception as e:
        await websocket.send_json({"type": "error", "message": str(e)})


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
