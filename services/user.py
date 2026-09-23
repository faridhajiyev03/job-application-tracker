from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from models.user import User
from schemas.user import UserCreate
from security import hash_password, verify_password


def get_user_by_email_service(email: str, db: Session):
    statement = select(User).where(User.email == email)
    result = db.execute(statement)

    return result.scalars().first()


def create_user_service(user: UserCreate, db: Session):
    existing_user = get_user_by_email_service(
        email=user.email,
        db=db,
    )

    if existing_user is not None:
        return None

    db_user = User(
        email=user.email,
        hashed_password=hash_password(user.password),
    )

    db.add(db_user)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise

    db.refresh(db_user)

    return db_user

def authenticate_user_service(
    email: str,
    password: str,
    db: Session,
):
    db_user = get_user_by_email_service(email=email, db=db)

    if db_user is None:
        return None

    if not verify_password(password, db_user.hashed_password):
        return None

    return db_user