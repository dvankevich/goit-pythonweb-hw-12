from fastapi import APIRouter, Depends, File, Request, UploadFile
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.session import get_db
from src.services.upload_file import UploadFileService
from src.services.users import UserService
from src.models.user import User
from src.services.auth import get_current_user, get_current_admin_user
from src.schemas.user import UserResponse

router = APIRouter(prefix="/users", tags=["users"])
limiter = Limiter(key_func=get_remote_address)


@router.get(
    "/me",
    response_model=UserResponse,
    description="No more than 10 requests per minute",
)
@limiter.limit("10/minute")
async def me(request: Request, user: User = Depends(get_current_user)):
    return user


@router.patch("/avatar", response_model=UserResponse)
async def update_avatar_user(
    file: UploadFile = File(...),
    user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    upload_service = UploadFileService()
    avatar_url = upload_service.upload_file(file, user.username)

    user_service = UserService(db)
    updated_user = await user_service.update_avatar_url(user.email, avatar_url)

    return updated_user
