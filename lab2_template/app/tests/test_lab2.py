import pytest
from app import app

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

# ===== ТЕСТЫ ДЛЯ ПАРАМЕТРОВ URL =====
def test_request_params_status(client):
    response = client.get("/request-params/")
    assert response.status_code == 200

def test_request_params_display(client):
    response = client.get("/request-params/?name=John&age=25")
    assert "name" in response.text
    assert "John" in response.text
    assert "age" in response.text
    assert "25" in response.text

# ===== ТЕСТЫ ДЛЯ ЗАГОЛОВКОВ =====
def test_request_headers_status(client):
    response = client.get("/request-headers/")
    assert response.status_code == 200

def test_request_headers_display(client):
    response = client.get("/request-headers/", headers={"User-Agent": "TestBrowser"})
    assert "User-Agent" in response.text

# ===== ТЕСТЫ ДЛЯ COOKIE =====
def test_cookies_status(client):
    response = client.get("/cookies/")
    assert response.status_code == 200

def test_cookie_set(client):
    response = client.get("/cookies/")
    assert 'user_choice' in response.headers.get('Set-Cookie', '')

def test_cookie_delete(client):
    response = client.get("/delete-cookie/")
    assert response.status_code == 302

# ===== ТЕСТЫ ДЛЯ ФОРМЫ =====
def test_form_params_status(client):
    response = client.get("/form-params/")
    assert response.status_code == 200

def test_form_params_post(client):
    response = client.post("/form-params/", data={'name': 'Test'})
    assert 'Test' in response.text

# ===== ТЕСТЫ ДЛЯ ВАЛИДАЦИИ ТЕЛЕФОНА =====
def test_phone_validation_status(client):
    response = client.get("/phone-validation/")
    assert response.status_code == 200

def test_valid_phone_plus7(client):
    response = client.post("/phone-validation/", data={'phone': '+7 (123) 456-75-90'})
    assert 'Номер корректен' in response.text
    assert '8-123-456-75-90' in response.text

def test_valid_phone_with_8(client):
    response = client.post("/phone-validation/", data={'phone': '8(123)4567590'})
    assert 'Номер корректен' in response.text

def test_valid_phone_with_dots(client):
    response = client.post("/phone-validation/", data={'phone': '123.456.75.90'})
    assert 'Номер корректен' in response.text

def test_invalid_phone_wrong_digits(client):
    response = client.post("/phone-validation/", data={'phone': '123'})
    assert 'Неверное количество цифр' in response.text
    assert 'is-invalid' in response.text

def test_invalid_phone_invalid_symbols(client):
    response = client.post("/phone-validation/", data={'phone': '+7 ABC 123'})
    assert 'недопустимые символы' in response.text

def test_bootstrap_invalid_class(client):
    response = client.post("/phone-validation/", data={'phone': '123'})
    assert 'is-invalid' in response.text

def test_bootstrap_feedback_class(client):
    response = client.post("/phone-validation/", data={'phone': '123'})
    assert 'invalid-feedback' in response.text

def test_footer_exists(client):
    response = client.get("/")
    assert "Отхонова Амуланга Александровна" in response.text
    assert "241-371" in response.text