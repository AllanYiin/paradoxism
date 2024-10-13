
from fastapi import APIRouter, Request, Depends, HTTPException
from sqlalchemy.orm import Session
from db import SessionLocal, add_api_record
import importlib.util
import os

router = APIRouter()

# 存儲動態 API 的路由
dynamic_routes = {}

# 動態加載並部署 API
@router.post("/deploy/{user}/{api_name}")
async def deploy_api(user: str, api_name: str, code: str, db: Session = Depends(SessionLocal)):
    # 檢查用戶名是否與路由前綴重疊
    if user in dynamic_routes:
        raise HTTPException(status_code=400, detail="路由前綴與用戶名重疊")

    # 儲存代碼並加載
    filename = f"{user}_{api_name}.py"
    with open(filename, "w") as f:
        f.write(code)
    
    spec = importlib.util.spec_from_file_location(api_name, filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    # 添加 API 路由
    for name in dir(module):
        func = getattr(module, name)
        if callable(func):
            route_path = f"/{user}/{api_name}/{name}"
            router.add_api_route(route_path, func, methods=["POST"])
            dynamic_routes[route_path] = func
    
    return {"status": "success", "route": f"/{user}/{api_name}"}
