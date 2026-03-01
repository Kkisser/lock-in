from aiogram import Router

from handlers.common import router as common_router
from handlers.now import router as now_router
from handlers.session import router as session_router
from handlers.today import router as today_router
from handlers.editor import router as editor_router
from handlers.settings import router as settings_router
from handlers.longterm import router as longterm_router


def setup_routers() -> Router:
    root = Router()
    root.include_router(common_router)
    root.include_router(now_router)
    root.include_router(session_router)
    root.include_router(today_router)
    root.include_router(editor_router)
    root.include_router(settings_router)
    root.include_router(longterm_router)
    return root
