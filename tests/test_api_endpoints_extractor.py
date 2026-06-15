"""Tests for the API endpoint extractor."""
from pathlib import Path

from repo_notes.extractors.api_endpoints import ApiEndpointExtractor
from repo_notes.scanner import FileInfo


def test_empty_project():
    result = ApiEndpointExtractor().extract(Path("/root"), [])
    assert result.endpoints == []


def test_flask_route(tmp_path: Path):
    f = tmp_path / "app.py"
    f.write_text("from flask import Flask\napp = Flask(__name__)\n@app.route('/api/users')\ndef get_users():\n    return 'ok'\n")
    files = [FileInfo(f, Path("app.py"), 80, ".py", False)]
    result = ApiEndpointExtractor().extract(tmp_path, files)
    assert len(result.endpoints) == 1
    ep = result.endpoints[0]
    assert ep["framework"] == "Flask"
    assert ep["path"] == "/api/users"


def test_fastapi_methods(tmp_path: Path):
    f = tmp_path / "main.py"
    f.write_text("from fastapi import FastAPI\napp = FastAPI()\n@app.get('/items')\ndef list_items(): pass\n@app.post('/items')\ndef create_item(): pass\n")
    files = [FileInfo(f, Path("main.py"), 100, ".py", False)]
    result = ApiEndpointExtractor().extract(tmp_path, files)
    assert len(result.endpoints) == 2
    methods = {ep["method"] for ep in result.endpoints}
    assert methods == {"GET", "POST"}


def test_django_urlpatterns(tmp_path: Path):
    f = tmp_path / "urls.py"
    f.write_text("from django.urls import path\nurlpatterns = [\n    path('admin/', admin.site.urls),\n    path('api/users', include('users.urls')),\n]\n")
    files = [FileInfo(f, Path("urls.py"), 100, ".py", False)]
    result = ApiEndpointExtractor().extract(tmp_path, files)
    assert len(result.endpoints) == 2
    assert result.endpoints[0]["framework"] == "Django"


def test_express_route(tmp_path: Path):
    f = tmp_path / "server.js"
    f.write_text("const app = express();\napp.get('/api/health', (req, res) => res.send('ok'));\napp.post('/api/items', handler);\n")
    files = [FileInfo(f, Path("server.js"), 100, ".js", False)]
    result = ApiEndpointExtractor().extract(tmp_path, files)
    assert len(result.endpoints) == 2
    methods = {ep["method"] for ep in result.endpoints}
    assert methods == {"GET", "POST"}
    assert all(ep["framework"] == "Express" for ep in result.endpoints)


def test_rails_routes(tmp_path: Path):
    d = tmp_path / "config"
    d.mkdir()
    f = d / "routes.rb"
    f.write_text("Rails.application.routes.draw do\n  get 'users/index'\n  resources :posts\nend\n")
    files = [FileInfo(f, Path("config/routes.rb"), 70, ".rb", False)]
    result = ApiEndpointExtractor().extract(tmp_path, files)
    assert len(result.endpoints) == 2
    frameworks = {ep["framework"] for ep in result.endpoints}
    assert frameworks == {"Rails"}


def test_ignores_binary_files(tmp_path: Path):
    f = tmp_path / "app.pyc"
    f.write_bytes(b"\x00\x01\x02")
    files = [FileInfo(f, Path("app.pyc"), 3, ".pyc", True)]
    result = ApiEndpointExtractor().extract(tmp_path, files)
    assert result.endpoints == []
