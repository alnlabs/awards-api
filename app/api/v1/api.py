from fastapi import APIRouter

from app.api.v1 import auth, users, forms, nominations, awards, cycles

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(auth.router, prefix="/auth", tags=["Auth"])
api_router.include_router(users.router, prefix="/users", tags=["Users"])
api_router.include_router(cycles.router, prefix="/cycles", tags=["Cycles"])
api_router.include_router(forms.router, prefix="/forms", tags=["Forms"])
api_router.include_router(nominations.router, prefix="/nominations", tags=["Nominations"])
api_router.include_router(awards.router, prefix="/awards", tags=["Awards"])


@api_router.get("/health", tags=["Health"])
def health():
    return {"status": "ok"}