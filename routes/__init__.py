from fastapi import APIRouter
from .student_routes import router as student_router
from .room_routes import router as room_router
from .assignment_routes import router as assignment_router

router = APIRouter()

router.include_router(student_router)
router.include_router(room_router)
router.include_router(assignment_router)
