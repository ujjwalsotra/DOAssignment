import pytest
from fastapi.testclient import TestClient
from main import app, repo

client = TestClient(app)

@pytest.fixture(autouse=True)
def clear_db():
    from database import engine, Base
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield

# ✅ Unit Test 1 — health check
def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "200-Healthy"}

# ✅ Unit Test 2 — shorten basic URL
def test_shorten_url():
    response = client.post("/shorten", json={
        "long_url": "https://www.google.com"
    })
    assert response.status_code == 201
    data = response.json()
    assert "short_code" in data
    assert "short_url" in data
    assert data["long_url"] == "https://www.google.com"
    assert data["access_count"] == 0

# ✅ Unit Test 3 — custom alias
def test_custom_alias():
    response = client.post("/shorten", json={
        "long_url": "https://www.github.com",
        "custom_alias": "github"
    })
    assert response.status_code == 201
    assert response.json()["short_code"] == "github"

# ✅ Unit Test 4 — duplicate custom alias returns 409
def test_duplicate_alias():
    client.post("/shorten", json={
        "long_url": "https://www.github.com",
        "custom_alias": "github"
    })
    response = client.post("/shorten", json={
        "long_url": "https://www.youtube.com",
        "custom_alias": "github"
    })
    assert response.status_code == 409
    assert "already taken" in response.json()["detail"]

# ✅ Unit Test 5 — metadata endpoint
def test_get_metadata():
    client.post("/shorten", json={
        "long_url": "https://www.google.com",
        "custom_alias": "meta-test"
    })
    response = client.get("/meta/meta-test")
    assert response.status_code == 200
    data = response.json()
    assert data["short_code"] == "meta-test"
    assert data["access_count"] == 0
    assert "created_at" in data

# ✅ Unit Test 6 — 404 for missing short code
def test_metadata_not_found():
    response = client.get("/meta/doesnotexist")
    assert response.status_code == 404

# ✅ Unit Test 7 — invalid URL returns 422
def test_invalid_input():
    response = client.post("/shorten", json={})
    assert response.status_code == 422

# ✅ Integration Test 1 — redirect follows to long url
def test_redirect():
    client.post("/shorten", json={
        "long_url": "https://www.google.com",
        "custom_alias": "redirect-test"
    })
    response = client.get("/redirect-test", follow_redirects=False)
    assert response.status_code == 307
    assert response.headers["location"] == "https://www.google.com"

# ✅ Integration Test 2 — access count increments on redirect
def test_access_count_increments():
    client.post("/shorten", json={
        "long_url": "https://www.google.com",
        "custom_alias": "count-test"
    })
    # hit redirect 3 times
    client.get("/count-test", follow_redirects=False)
    client.get("/count-test", follow_redirects=False)
    client.get("/count-test", follow_redirects=False)

    response = client.get("/meta/count-test")
    assert response.json()["access_count"] == 3

# ✅ Integration Test 3 — cache hit vs miss
def test_cache_behaviour():
    client.post("/shorten", json={
        "long_url": "https://www.google.com",
        "custom_alias": "cache-test"
    })
    # first hit — cache miss, goes to DB
    r1 = client.get("/cache-test", follow_redirects=False)
    assert r1.status_code == 307

    # second hit — cache hit
    r2 = client.get("/cache-test", follow_redirects=False)
    assert r2.status_code == 307
    assert r2.headers["location"] == "https://www.google.com"
