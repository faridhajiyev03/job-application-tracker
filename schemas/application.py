from pydantic import BaseModel, ConfigDict, Field, field_validator
from models.application_status import ApplicationStatus

class ApplicationCreate(BaseModel):
    company: str = Field(min_length=1, max_length=100)
    position: str = Field(min_length=1, max_length=100)
    vacancy_url: str | None = None
    notes: str | None = None

class ApplicationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    company: str
    position: str
    vacancy_url: str | None
    notes: str | None
    status: ApplicationStatus

class ApplicationUpdate(BaseModel):
    company: str | None = Field(
        default=None,
        min_length=1,
        max_length=100,
    )
    position: str | None = Field(
        default=None,
        min_length=1,
        max_length=100,
    )
    vacancy_url: str | None = None
    notes: str | None = None
    status: ApplicationStatus | None = None

    @field_validator("company", "position", "status")
    @classmethod
    def reject_null(cls, value: str | None) -> str:
        if value is None:
            raise ValueError("Field cannot be null")

        return value

class ApplicationSummary(BaseModel):
    total: int
    applied: int
    interview: int
    offer: int
    rejected: int