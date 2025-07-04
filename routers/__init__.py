from .quiz_router import router as quiz_router
from .user_router import router as user_router
from .admin_router import router as admin_router
app.include_router(quiz_router, prefix="/quiz")
app.include_router(user_router, prefix="/user")
app.include_router(admin_router, prefix="/admin")
