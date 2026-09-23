from sqlalchemy import String, Text, Enum as SAEnum, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from models.application_status import ApplicationStatus
from database import Base

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from models.user import User

class Application(Base):
    __tablename__ = "applications"

    id: Mapped[int] = mapped_column(primary_key=True)
    company: Mapped[str] = mapped_column(String(100))
    position: Mapped[str] = mapped_column(String(100))
    vacancy_url: Mapped[str | None] = mapped_column(Text)
    notes: Mapped[str | None] = mapped_column(Text)
    status: Mapped[ApplicationStatus] = mapped_column(
        SAEnum(
            ApplicationStatus,
            name="application_status",
            native_enum=False,
            create_constraint=True,
            values_callable=lambda enum_class: [
                item.value for item in enum_class
            ],
        ),
        nullable=False,
        default=ApplicationStatus.APPLIED,
        server_default="applied",
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey(
            "users.id",
            name="fk_applications_user_id_users",
        ),
        nullable=False,
    )

    user: Mapped["User"] = relationship(
        "User",
        back_populates="applications",
    )