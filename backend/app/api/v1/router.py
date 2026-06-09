from fastapi import APIRouter

from app.api.v1 import auth, gateway_logs, health, llm
from app.api.v1.faculty.router import router as faculty_router
from app.api.v1.student.router import router as student_router

api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(gateway_logs.router, prefix="/gateway", tags=["gateway"])
api_router.include_router(llm.router, prefix="/llm", tags=["llm"])
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(faculty_router, prefix="/faculty", tags=["faculty"])
api_router.include_router(student_router, prefix="/student", tags=["student"])
