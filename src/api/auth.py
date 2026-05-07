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


# User registration
@router.post("/register", response_model=User, status_code=status.HTTP_201_CREATED)
async def register_user(
    user_data: UserCreate,
    background_tasks: BackgroundTasks,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Register a new user.
    
    Args:
        user_data: User registration data including email, username, and password.
        background_tasks: FastAPI background tasks for email verification.
        request: HTTP request object for base URL extraction.
        db: Async database session.
    
    Returns:
        User: The newly created user object.
    
    Raises:
        HTTPException: If user with email or username already exists.
    """
    user_service = UserService(db)

    email_user = await user_service.get_user_by_email(user_data.email)
    if email_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User with this email already exists",
        )

    username_user = await user_service.get_user_by_username(user_data.username)
    if username_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User with this name already exists",
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
    db: AsyncSession = Depends(get_db),  # 3. Specify AsyncSession type
):
    """Authenticate user and return access token.
    
    Args:
        form_data: OAuth2 password request form with username and password.
        db: Async database session.
    
    Returns:
        Token: JWT access token with token type.
    
    Raises:
        HTTPException: If credentials are invalid or email not confirmed.
    """
    user_service = UserService(db)
    user = await user_service.get_user_by_username(form_data.username)

    if not user or not Hash().verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid login or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.confirmed:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email address not confirmed",
        )

    access_token = await create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/confirmed_email/{token}")
async def confirmed_email(token: str, db: AsyncSession = Depends(get_db)):
    """Confirm user email using verification token.
    
    Args:
        token: Email verification token.
        db: Async database session.
    
    Returns:
        dict: Confirmation message.
    
    Raises:
        HTTPException: If token is invalid or user not found.
    """
    email = await get_email_from_token(token)
    user_service = UserService(db)
    user = await user_service.get_user_by_email(email)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Verification error"
        )
    if user.confirmed:
        return {"message": "Your email is already confirmed"}
    await user_service.confirmed_email(email)
    return {"message": "Email confirmed"}


@router.post("/request_email")
@limiter.limit("3/minute")
async def request_email(
    body: RequestEmail,
    background_tasks: BackgroundTasks,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Request email verification for existing user.
    
    Rate limited to 3 requests per minute to prevent abuse.
    
    Args:
        body: Request body containing user email.
        background_tasks: FastAPI background tasks for email sending.
        request: HTTP request object for base URL extraction.
        db: Async database session.
    
    Returns:
        dict: Generic message about email verification.
    """
    user_service = UserService(db)
    user = await user_service.get_user_by_email(body.email)

    # To prevent enumeration, return one message for all cases
    generic_message = {
        "message": "If your address is in our database, you will receive a confirmation letter within a few minutes."
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
    """Request password reset email.
    
    Rate limited to 3 requests per minute to prevent abuse.
    
    Args:
        body: Request body containing user email.
        background_tasks: FastAPI background tasks for email sending.
        request: HTTP request object for base URL extraction.
        db: Async database session.
    
    Returns:
        dict: Message about password reset instructions.
    """
    user_service = UserService(db)
    user = await user_service.get_user_by_email(body.email)

    if user:
        # Send email in background
        background_tasks.add_task(
            send_reset_password_email, user.email, user.username, str(request.base_url)
        )

    return {
        "message": "If your address is in our database, you will receive a letter with password reset instructions."
    }


@router.post("/reset_password/{token}")
async def reset_password(
    token: str, body: ResetPassword, db: AsyncSession = Depends(get_db)
):
    """Reset user password using reset token.
    
    Args:
        token: Password reset token.
        body: Request body containing new password.
        db: Async database session.
    
    Returns:
        dict: Success message.
    
    Raises:
        HTTPException: If token is invalid or user not found.
    """
    # Get email from token
    email = await get_email_from_token(token)

    user_service = UserService(db)
    user = await user_service.get_user_by_email(email)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid token or user not found",
        )

    # Hash new password and save
    hashed_password = Hash().get_password_hash(body.new_password)
    await user_service.update_password(email, hashed_password)

    # Invalidate Redis cache for this user so they must login again
    from src.services.auth import redis_client

    await redis_client.delete(f"user:{user.username}")

    return {"message": "Password successfully changed"}
