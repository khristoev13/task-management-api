from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, status
from sqlmodel import Session, select

from app.database import create_db_and_tables, get_session
from app.models import Task, TaskCreate, TaskResponse, TaskUpdate

SessionDep = Annotated[Session, Depends(get_session)]


@asynccontextmanager
async def lifespan(app: FastAPI):
    if not app.dependency_overrides:
        create_db_and_tables()

    yield


app = FastAPI(
    title="Task Management API",
    description="A REST API for managing tasks",
    version="1.0.0",
    lifespan=lifespan,
)


@app.get("/health")
def health_check():
    return {"status": "ok", "message": "Task Management API is running"}


@app.post(
    "/tasks",
    response_model=TaskResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_task(
    task: TaskCreate,
    session: SessionDep,
):
    db_task = Task(**task.model_dump())

    session.add(db_task)
    session.commit()
    session.refresh(db_task)

    return db_task


@app.get("/tasks", response_model=list[TaskResponse])
def get_tasks(session: SessionDep):
    statement = select(Task)
    return session.exec(statement).all()


@app.get("/tasks/{task_id}", response_model=TaskResponse)
def get_task(
    task_id: int,
    session: SessionDep,
):
    task = session.get(Task, task_id)

    if task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        )

    return task


@app.patch("/tasks/{task_id}", response_model=TaskResponse)
def update_task(
    task_id: int,
    task_update: TaskUpdate,
    session: SessionDep,
):
    db_task = session.get(Task, task_id)

    if db_task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        )

    update_data = task_update.model_dump(exclude_unset=True)

    if update_data.get("title") is None and "title" in update_data:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Title cannot be null",
        )

    if update_data.get("status") is None and "status" in update_data:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Status cannot be null",
        )

    db_task.sqlmodel_update(update_data)

    session.add(db_task)
    session.commit()
    session.refresh(db_task)

    return db_task


@app.delete(
    "/tasks/{task_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_task(
    task_id: int,
    session: SessionDep,
):
    task = session.get(Task, task_id)

    if task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        )

    session.delete(task)
    session.commit()
