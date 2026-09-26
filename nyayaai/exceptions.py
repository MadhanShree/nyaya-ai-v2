from fastapi import HTTPException


def bad_request(message: str) -> HTTPException:
    return HTTPException(status_code=400, detail=message)


def too_large(message: str) -> HTTPException:
    return HTTPException(status_code=413, detail=message)
