import pytest
from faker import Faker
from fastapi.testclient import TestClient

fake = Faker()


def test_health_check(client: TestClient):
    response = client.get("/health")

    assert response.status_code == 200, response.text
    assert response.json()["status"] == "ok"


def test_create_task(client: TestClient):
    payload = {"title": "Learn PyTest", "description": "Created automated API tests"}
    response = client.post("/tasks", json=payload)

    assert response.status_code == 201, response.text

    body = response.json()

    assert isinstance(body["id"], int)
    assert body["id"] >= 1
    assert body["title"] == payload["title"]
    assert body["description"] == payload["description"]
    assert body["status"] == "todo"
    assert body["created_at"] is not None


def test_get_all_tasks(client: TestClient):
    first_task = client.post("/tasks", json={"title": "Task 1"})
    assert first_task.status_code == 201, first_task.text

    second_task = client.post("/tasks", json={"title": "Task 2"})
    assert second_task.status_code == 201, second_task.text

    response = client.get("/tasks")

    assert response.status_code == 200, response.text

    tasks = response.json()

    assert len(tasks) == 2
    assert {task["title"] for task in tasks} == {"Task 1", "Task 2"}


def test_get_task_by_id(client: TestClient):
    create_response = client.post("/tasks", json={"title": "Test task"})
    assert create_response.status_code == 201, create_response.text

    task_id = create_response.json()["id"]

    response = client.get(f"/tasks/{task_id}")

    assert response.status_code == 200, response.text
    assert response.json()["id"] == task_id


@pytest.mark.parametrize(
    "initial_status, new_status",
    [
        pytest.param("todo", "in_progress", id="todo_to_in_progress"),
        pytest.param("todo", "done", id="todo_to_done"),
        pytest.param("in_progress", "todo", id="in_progress_to_todo"),
        pytest.param("in_progress", "done", id="in_progress_to_done"),
        pytest.param("done", "todo", id="done_to_todo"),
        pytest.param("done", "in_progress", id="done_to_in_progress"),
    ],
)
def test_update_task_status(
    client: TestClient,
    initial_status: str,
    new_status: str,
):
    # arrange
    create_response = client.post(
        "/tasks",
        json={"title": fake.word()},
    )

    assert create_response.status_code == 201, create_response.text

    task_id = create_response.json()["id"]

    setup_response = client.patch(
        f"/tasks/{task_id}",
        json={"status": initial_status},
    )

    assert setup_response.status_code == 200, setup_response.text

    original_task = setup_response.json()

    assert original_task["status"] == initial_status

    # act
    response = client.patch(
        f"/tasks/{task_id}",
        json={"status": new_status},
    )

    # assert
    assert response.status_code == 200, response.text

    expected_task = {
        **original_task,
        "status": new_status,
    }

    assert response.json() == expected_task

    # verify persistence
    get_response = client.get(f"/tasks/{task_id}")

    assert get_response.status_code == 200, get_response.text
    assert get_response.json() == expected_task


def test_delete_task(client: TestClient):
    create_response = client.post("/tasks", json={"title": "Task to delete"})
    assert create_response.status_code == 201, create_response.text

    task_id = create_response.json()["id"]

    delete_response = client.delete(f"/tasks/{task_id}")

    assert delete_response.status_code == 204, delete_response.text

    get_response = client.get(f"/tasks/{task_id}")

    assert get_response.status_code == 404, get_response.text


def test_get_non_existent_task(client: TestClient):
    non_existent_id = 9999

    response = client.get(f"/tasks/{non_existent_id}")

    assert response.status_code == 404, response.text
    assert response.json()["detail"] == "Task not found"


def test_create_task_without_title(client: TestClient):
    payload = {"description": fake.sentence()}
    response = client.post("/tasks", json=payload)

    assert response.status_code == 422, response.text

    error = response.json()["detail"][0]
    assert error["type"] == "missing"
    assert error["loc"] == ["body", "title"]
    assert error["msg"] == "Field required"

    # verify that no task was created
    get_response = client.get("/tasks")

    assert get_response.status_code == 200, get_response.text
    assert get_response.json() == []


def test_update_task_title(client: TestClient):
    old_title = fake.word()
    new_title = f"Updated {old_title}"

    payload = {"title": old_title, "description": fake.sentence()}

    create_response = client.post("/tasks", json=payload)

    assert create_response.status_code == 201, create_response.text

    original_task = create_response.json()
    task_id = original_task["id"]

    response = client.patch(f"/tasks/{task_id}", json={"title": new_title})

    assert response.status_code == 200, response.text

    updated_task = response.json()

    expected_task = {**original_task, "title": new_title}  # unpack the whole dictionary

    assert updated_task == expected_task

    # verify persistence
    get_response = client.get(f"/tasks/{task_id}")

    assert get_response.status_code == 200, get_response.text
    assert get_response.json() == updated_task


@pytest.mark.parametrize(
    "title, expected_error_type",
    [
        pytest.param("", "string_too_short", id="title_too_short"),
        pytest.param("a" * 101, "string_too_long", id="title_too_long"),
        pytest.param(123, "string_type", id="numeric_title"),
        pytest.param(None, "string_type", id="null_title"),
    ],
)
def test_create_task_with_invalid_title(
    client: TestClient, title: str | int | None, expected_error_type: str
):
    payload = {"title": title}
    response = client.post("/tasks", json=payload)

    assert response.status_code == 422, response.text

    error = response.json()["detail"][0]
    assert error["type"] == expected_error_type
    assert error["loc"] == ["body", "title"]

    # verify that no task was created
    get_response = client.get("/tasks")

    assert get_response.status_code == 200, get_response.text
    assert get_response.json() == []


@pytest.mark.parametrize(
    "title_length, expected_status, expected_error_type",
    [
        pytest.param(0, 422, "string_too_short", id="out_of_range_value_min"),
        pytest.param(1, 201, None, id="min_valid_length"),
        pytest.param(2, 201, None, id="short_valid_length"),
        pytest.param(50, 201, None, id="mid_valid_length"),
        pytest.param(99, 201, None, id="long_valid_length"),
        pytest.param(100, 201, None, id="max_valid_length"),
        pytest.param(101, 422, "string_too_long", id="out_of_range_value_max"),
    ],
)
def test_create_task_title_boundary_values(
    client: TestClient,
    title_length: int,
    expected_status: int,
    expected_error_type: str | None,
):
    title = "a" * title_length
    payload = {"title": title}

    response = client.post("/tasks", json=payload)

    assert response.status_code == expected_status, response.text

    if expected_status == 201:
        created_task = response.json()

        assert created_task["title"] == title
        assert len(created_task["title"]) == title_length

    else:
        error = response.json()["detail"][0]
        assert error["type"] == expected_error_type
        assert error["loc"] == ["body", "title"]

        tasks_response = client.get("/tasks")
        assert tasks_response.status_code == 200, tasks_response.text
        assert tasks_response.json() == []


@pytest.mark.parametrize(
    "invalid_task_status, expected_status_code, expected_error_type",
    [
        pytest.param("completed", 422, "enum", id="invalid_task_status_completed"),
        pytest.param("TODO", 422, "enum", id="invalid_task_status_todo_uppercase"),
        pytest.param("", 422, "enum", id="invalid_task_status_empty_string"),
        pytest.param(123, 422, "enum", id="invalid_task_status_number"),
        pytest.param(None, 422, None, id="invalid_task_status_none"),
    ],
)
def test_update_task_with_invalid_status(
    client: TestClient,
    invalid_task_status: str | int | None,
    expected_status_code: int,
    expected_error_type: str | None,
):
    initial_title = "Title of valid task"
    initial_description = "Description of valid task"

    initial_payload = {
        "title": initial_title,
        "description": initial_description,
    }

    initial_response = client.post("/tasks", json=initial_payload)

    assert initial_response.status_code == 201, initial_response.text

    original_task = initial_response.json()
    task_id = original_task["id"]

    updated_payload = {"status": invalid_task_status}
    updated_response = client.patch(f"/tasks/{task_id}", json=updated_payload)

    assert updated_response.status_code == expected_status_code, updated_response.text

    error_detail = updated_response.json()["detail"]

    if expected_error_type is not None:
        error = error_detail[0]

        assert error["type"] == expected_error_type
        assert error["loc"] == ["body", "status"]

    else:
        assert error_detail == "Status cannot be null"

    # verify that task wasn't updated
    get_response = client.get(f"/tasks/{task_id}")

    assert get_response.status_code == 200, get_response.text
    assert get_response.json() == original_task
