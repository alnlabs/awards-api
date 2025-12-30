from fastapi import APIRouter

from app.api.v1 import auth, users, forms, nominations, awards, panels

router = APIRouter()

router.include_router(auth.router, prefix="/auth", tags=["Auth"])
router.include_router(users.router, prefix="/users", tags=["Users"])
router.include_router(forms.router, prefix="/forms", tags=["Forms"])
router.include_router(nominations.router, prefix="/nominations", tags=["Nominations"])
router.include_router(awards.router, prefix="/awards", tags=["Awards"])
router.include_router(panels.router, prefix="/panels", tags=["Panels"])


@router.get("/health", tags=["Health"])
def health():
    return {"status": "ok"}