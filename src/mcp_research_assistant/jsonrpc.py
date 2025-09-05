from __future__ import annotations

from typing import Any, Dict
import inspect
from pydantic import BaseModel
from fastapi import APIRouter, HTTPException

router = APIRouter()

class JSONRPCRequest(BaseModel):
    jsonrpc: str
    method: str
    params: Dict[str, Any] | None = None
    id: str | int | None = None

class JSONRPCResponse(BaseModel):
    jsonrpc: str = "2.0"
    result: Any | None = None
    error: Dict[str, Any] | None = None
    id: str | int | None = None

method_registry: dict[str, Any] = {}

def rpc_method(name: str):
    def decorator(func):
        method_registry[name] = func
        return func
    return decorator

@router.post("/json-rpc")
async def handle_jsonrpc(request: JSONRPCRequest):
    if request.jsonrpc != "2.0":
        raise HTTPException(status_code=400, detail="Invalid JSON-RPC version")
    if request.method not in method_registry:
        return JSONRPCResponse(id=request.id, error={"code": -32601, "message": "Method not found"})
    try:
        func = method_registry[request.method]
        params = request.params or {}
        if inspect.iscoroutinefunction(func):
            result = await func(**params)
        else:
            result = func(**params)
        return JSONRPCResponse(id=request.id, result=result)
    except Exception as e:
        return JSONRPCResponse(id=request.id, error={"code": -32000, "message": str(e)})
