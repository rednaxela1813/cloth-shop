import pytest

pytestmark = pytest.mark.django_db


def test_404_uses_template(client):
    resp = client.get("/this-page-does-not-exist-404/")
    assert resp.status_code == 404
    # Django test client хранит использованные шаблоны
    template_names = [t.name for t in resp.templates if t.name]
    assert "404.html" in template_names
