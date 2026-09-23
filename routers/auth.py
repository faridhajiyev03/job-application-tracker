from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from database import get_db
from schemas.user import UserCreate, UserResponse, UserLogin, TokenResponse
from services.user import create_user_service, authenticate_user_service
from security import create_access_token, get_current_user
from models.user import User


router = APIRouter(
    prefix="/auth",
    tags=["Auth"],
)

@router.get("/me", response_model=UserResponse)
def get_me(
    current_user: User = Depends(get_current_user),
):
    return current_user


@router.post("/register", response_model=UserResponse, status_code=201)
def register(
    user: UserCreate,
    db: Session = Depends(get_db),
):
    try:
        db_user = create_user_service(user=user, db=db)
    except IntegrityError as error:
        if getattr(error.orig, "sqlstate", None) == "23505":
            raise HTTPException(
                status_code=409,
                detail="Email already registered",
            ) from error

        raise

    if db_user is None:
        raise HTTPException(
            status_code=409,
            detail="Email already registered",
        )

    return db_user

@router.post("/login", response_model=TokenResponse)
def login(
    credentials: UserLogin,
    db: Session = Depends(get_db),
):
    db_user = authenticate_user_service(
        email=credentials.email,
        password=credentials.password,
        db=db,
    )

    if db_user is None:
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password",
        )

    access_token = create_access_token(user_id=db_user.id)

    return TokenResponse(access_token=access_token)

