"""Ensamble e inicio: SQLite + servicio + ReactPy servido por FastAPI."""
import logging
import os

from fastapi import FastAPI
from reactpy import component
from reactpy.backend.fastapi import configure

from app.adapters.sqlite_repo import SQLiteRepository
from app.ui.components import App
from app.ui.service import AppService

logging.basicConfig(level=logging.INFO)


def create_app(db_path: str | None = None) -> FastAPI:
    repo = SQLiteRepository(db_path or os.environ.get("GESTOR_DB", "gestor.db"))
    service = AppService(repo)

    @component
    def Root():
        return App(service)

    fastapi_app = FastAPI(title="Gestor de proyectos")
    configure(fastapi_app, Root)
    return fastapi_app


app = create_app()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)
