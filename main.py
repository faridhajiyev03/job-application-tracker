from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from routers.applications import router as applications_router
from routers.auth import router as auth_router


BASE_DIR = Path(__file__).resolve().parent
FRONTEND_DIST = BASE_DIR / "frontend" / "dist"

app = FastAPI(title="Job Application Tracker")

# Existing endpoints remain available.
app.include_router(auth_router)
app.include_router(applications_router)

# React uses the /api prefix in production.
app.include_router(auth_router, prefix="/api", include_in_schema=False)
app.include_router(
    applications_router,
    prefix="/api",
    include_in_schema=False,
)


@app.get("/health", include_in_schema=False)
def health():
    return {"status": "ok"}


if FRONTEND_DIST.is_dir():
    app.mount(
        "/assets",
        StaticFiles(directory=FRONTEND_DIST / "assets"),
        name="assets",
    )

    @app.get("/", include_in_schema=False)
    def frontend():
        return FileResponse(
            FRONTEND_DIST / "index.html",
            headers={"Cache-Control": "no-cache"},
        )

else:
    @app.get("/", include_in_schema=False)
    def read_root():
        return {"message": "Job Application Tracker API"}