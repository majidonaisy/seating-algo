from fastapi import APIRouter
from .student_routes import router as student_router
from .room_routes import router as room_router
from .assignment_routes import router as assignment_router
from .user_routes import router as user_router

router = APIRouter()

# Include all the specialized routers
router.include_router(student_router)
router.include_router(room_router)
router.include_router(assignment_router)
router.include_router(user_router)
