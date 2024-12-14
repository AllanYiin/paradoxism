from fastapi import FastAPI
from api_manager import router as api_router
from scheduler import scheduler

app = FastAPI()

# 包裝的 API 路由
app.include_router(api_router)

@app.on_event("startup")
async def startup():
    scheduler.start()

@app.on_event("shutdown")
async def shutdown():
    scheduler.shutdown()

# 定義主入口函數，支持自定義端口
def start_server():
    # 使用 argparse 解析命令行參數
    parser = argparse.ArgumentParser(description="Start the Paradoxism server.")
    parser.add_argument("--port", type=int, default=8765, help="Specify the port to run the server on.")
    args = parser.parse_args()

    # 啟動伺服器
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=args.port)