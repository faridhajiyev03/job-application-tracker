from sqlalchemy import select, func, or_
from sqlalchemy.orm import Session

from models.application import Application
from models.application_status import ApplicationStatus
from schemas.application import ApplicationCreate, ApplicationUpdate


def create_application_service(
    application: ApplicationCreate,
    db: Session,
    user_id: int,
):
    db_application = Application(
        company=application.company,
        position=application.position,
        vacancy_url=application.vacancy_url,
        notes=application.notes,
        user_id=user_id,
    )

    db.add(db_application)
    db.commit()
    db.refresh(db_application)

    return db_application


def get_applications_service(
    db: Session,
    user_id: int,
    status: ApplicationStatus | None = None,
    search: str | None = None,
    limit: int = 20,
    offset: int = 0,
):
    statement = select(Application).where(
        Application.user_id == user_id
    )

    if status is not None:
        statement = statement.where(Application.status == status)

    if search is not None:
        search_text = search.strip()

        if search_text:
            statement = statement.where(
                or_(
                    Application.company.icontains(
                        search_text,
                        autoescape=True,
                    ),
                    Application.position.icontains(
                        search_text,
                        autoescape=True,
                    ),
                )
            )

    statement = (
        statement
        .order_by(Application.id)
        .offset(offset)
        .limit(limit)
    )

    result = db.execute(statement)

    return result.scalars().all()


def get_application_by_id_service(
    application_id: int,
    db: Session,
    user_id: int,
):
    statement = select(Application).where(
        Application.id == application_id,
        Application.user_id == user_id,
    )

    result = db.execute(statement)

    return result.scalars().first()


def update_application_service(
    application_id: int,
    application: ApplicationUpdate,
    db: Session,
    user_id: int,
):
    db_application = get_application_by_id_service(
        application_id=application_id,
        db=db,
        user_id=user_id,
    )

    if db_application is None:
        return None

    changes = application.model_dump(exclude_unset=True)

    for field, value in changes.items():
        setattr(db_application, field, value)

    db.commit()
    db.refresh(db_application)

    return db_application


def delete_application_service(
    application_id: int,
    db: Session,
    user_id: int,
):
    db_application = get_application_by_id_service(
        application_id=application_id,
        db=db,
        user_id=user_id,
    )

    if db_application is None:
        return False

    db.delete(db_application)
    db.commit()

    return True

def get_application_summary_service(db: Session, user_id: int):
    statement = (
        select(Application.status, func.count(Application.id))
        .where(Application.user_id == user_id)
        .group_by(Application.status)
    )

    rows = db.execute(statement).all()

    summary = {
        "total": 0,
        "applied": 0,
        "interview": 0,
        "offer": 0,
        "rejected": 0,
    }

    for status, count in rows:
        summary[status.value] = count
        summary["total"] += count

    return summary