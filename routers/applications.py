from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy.orm import Session

from database import get_db
from models.application_status import ApplicationStatus
from models.user import User
from schemas.application import (
    ApplicationCreate,
    ApplicationResponse,
    ApplicationUpdate,
    ApplicationSummary
)
from security import get_current_user
from services.application import (
    create_application_service,
    get_applications_service,
    get_application_by_id_service,
    update_application_service,
    delete_application_service,
    get_application_summary_service
)


router = APIRouter(
    prefix="/applications",
    tags=["Applications"],
)


@router.get("/summary", response_model=ApplicationSummary)
def get_application_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return get_application_summary_service(
        db=db,
        user_id=current_user.id,
    )




@router.get("/", response_model=list[ApplicationResponse])
def get_applications(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    status: ApplicationStatus | None = None,
    search: str | None = Query(default=None, max_length=100),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
):
    return get_applications_service(
        db=db,
        user_id=current_user.id,
        status=status,
        search=search,
        limit=limit,
        offset=offset,
    )


@router.get("/{application_id}", response_model=ApplicationResponse)
def get_application(
    application_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    db_application = get_application_by_id_service(
        application_id=application_id,
        db=db,
        user_id=current_user.id,
    )

    if db_application is None:
        raise HTTPException(
            status_code=404,
            detail="Application not found",
        )

    return db_application


@router.post(
    "/",
    response_model=ApplicationResponse,
    status_code=201,
)
def create_application(
    application: ApplicationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return create_application_service(
        application=application,
        db=db,
        user_id=current_user.id,
    )

@router.patch("/{application_id}", response_model=ApplicationResponse)
def update_application(
    application_id: int,
    application: ApplicationUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    db_application = update_application_service(
        application_id=application_id,
        application=application,
        db=db,
        user_id=current_user.id,
    )

    if db_application is None:
        raise HTTPException(
            status_code=404,
            detail="Application not found",
        )

    return db_application


@router.delete("/{application_id}", status_code=204)
def delete_application(
    application_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    deleted = delete_application_service(
        application_id=application_id,
        db=db,
        user_id=current_user.id,
    )

    if not deleted:
        raise HTTPException(
            status_code=404,
            detail="Application not found",
        )

    return Response(status_code=204)