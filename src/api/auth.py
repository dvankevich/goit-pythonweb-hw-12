from fastapi import (
    APIRouter,
    HTTPException,
    Depends,
    status,
    Security,
    BackgroundTasks,
    Request,
)

from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.security import OAuth2PasswordRequestForm
from src.api.users import limiter
from src.db.session import get_db
from src.schemas.user import RequestEmail, Token, User, UserCreate, ResetPassword
from src.services.auth import create_access_token, Hash, get_email_from_token
from src.services.users import UserService
from src.services.email import send_verification_email, send_reset_password_email

router = APIRouter(prefix="/auth", tags=["auth"])


# Реєстрація користувача
@router.post("/register", response_model=User, status_code=status.HTTP_201_CREATED)
async def register_user(
    user_data: UserCreate,
    background_tasks: BackgroundTasks,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    user_service = UserService(db)

    email_user = await user_service.get_user_by_email(user_data.email)
    if email_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Користувач з таким email вже існує",
        )

    username_user = await user_service.get_user_by_username(user_data.username)
    if username_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Користувач з таким іменем вже існує",
        )

    user_data.password = Hash().get_password_hash(user_data.password)
    new_user = await user_service.create_user(user_data)
    background_tasks.add_task(
        send_verification_email, new_user.email, new_user.username, str(request.base_url)
    )

    return new_user


@router.post("/login", response_model=Token)
async def login_user(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),  # 3. Вказуємо тип AsyncSession
):
    user_service = UserService(db)
    user = await user_service.get_user_by_username(form_data.username)

    if not user or not Hash().verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неправильний логін або пароль",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.confirmed:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Електронна адреса не підтверджена",
        )

    access_token = await create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/confirmed_email/{token}")
async def confirmed_email(token: str, db: AsyncSession = Depends(get_db)):
    email = await get_email_from_token(token)
    user_service = UserService(db)
    user = await user_service.get_user_by_email(email)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Verification error"
        )
    if user.confirmed:
        return {"message": "Ваша електронна пошта вже підтверджена"}
    await user_service.confirmed_email(email)
    return {"message": "Електронну пошту підтверджено"}


@router.post("/request_email")
@limiter.limit("3/minute")
async def request_email(
    body: RequestEmail,
    background_tasks: BackgroundTasks,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    user_service = UserService(db)
    user = await user_service.get_user_by_email(body.email)

    # Щоб запобігти енумерації повертаємо одне повідомлення для всії випадків
    generic_message = {
        "message": "Якщо ваша адреса є у нашій базі, ви отримаєте лист для підтвердження протягом кількох хвилин."
    }

    if user is None:
        return generic_message

    if user.confirmed:
        return generic_message

    background_tasks.add_task(
        send_verification_email, user.email, user.username, str(request.base_url)
    )

    return generic_message


@router.post("/forgot_password")
@limiter.limit("3/minute")
async def forgot_password(
    body: RequestEmail,
    background_tasks: BackgroundTasks,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    user_service = UserService(db)
    user = await user_service.get_user_by_email(body.email)

    if user:
        # Відправляємо лист у бекграунді
        background_tasks.add_task(
            send_reset_password_email, user.email, user.username, str(request.base_url)
        )

    return {
        "message": "Якщо ваша адреса є у нашій базі, ви отримаєте лист з інструкціями щодо скидання пароля."
    }


@router.post("/reset_password/{token}")
async def reset_password(
    token: str, body: ResetPassword, db: AsyncSession = Depends(get_db)
):
    # Дістаємо email з токена
    email = await get_email_from_token(token)

    user_service = UserService(db)
    user = await user_service.get_user_by_email(email)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Недійсний токен або користувача не знайдено",
        )

    # Хешуємо новий пароль та зберігаємо
    hashed_password = Hash().get_password_hash(body.new_password)
    await user_service.update_password(email, hashed_password)

    # Інвалідуємо кеш Redis для цього користувача, щоб він мусив залогінитись наново
    from src.services.auth import redis_client

    await redis_client.delete(f"user:{user.username}")

    return {"message": "Пароль успішно змінено"}
