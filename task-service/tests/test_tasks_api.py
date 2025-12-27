def test_healthz(client):
    r = client.get("/healthz")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_requires_auth(client):
    r = client.get("/tasks")
    assert r.status_code in (401, 403)


def test_crud_flow(client, token):
    headers = {"Authorization": f"Bearer {token}"}

    # CREATE
    r1 = client.post("/tasks", json={"title": "t1", "description": "d1"}, headers=headers)
    assert r1.status_code == 201
    task = r1.json()
    assert task["title"] == "t1"
    task_id = task["id"]

    # LIST
    r2 = client.get("/tasks", headers=headers)
    assert r2.status_code == 200
    body = r2.json()
    assert "items" in body and isinstance(body["items"], list)
    assert any(x["id"] == task_id for x in body["items"])

    # UPDATE
    r3 = client.patch(f"/tasks/{task_id}", json={"status": "done"}, headers=headers)
    assert r3.status_code == 200
    updated = r3.json()
    assert updated["id"] == task_id
    assert updated["status"] == "done"

    # DELETE
    r4 = client.delete(f"/tasks/{task_id}", headers=headers)
    assert r4.status_code == 204

    # DELETE AGAIN -> 404
    r5 = client.delete(f"/tasks/{task_id}", headers=headers)
    assert r5.status_code == 404
