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

# 定義主入口函數
def start_server():
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8765)  # 使用不常見的端口 8765
