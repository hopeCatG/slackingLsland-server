from typing import Any


def success_response(data: Any = None, message: str = "success", code: int = 200) -> dict[str, Any]:
    return {"code": code, "data": data, "message": message}


def error_response(message: str, code: int, data: Any = None) -> dict[str, Any]:
    return {"code": code, "data": data, "message": message}
