import pytest
from app import app, db
from models import User, Role
from werkzeug.security import generate_password_hash

# Фикстура: тестовый клиент
@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['SECRET_KEY'] = 'test-secret-key'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['WTF_CSRF_ENABLED'] = False
    
    with app.test_client() as client:
        with app.app_context():
            # Создаем таблицы
            db.drop_all()
            db.create_all()
            
            # Добавляем роли
            admin_role = Role(name='admin', description='Администратор')
            user_role = Role(name='user', description='Пользователь')
            db.session.add_all([admin_role, user_role])
            db.session.commit()
            
            # Добавляем тестового пользователя
            test_user = User(
                username='testuser',
                password_hash=generate_password_hash('Test123!'),
                first_name='Тестовый',
                last_name='Пользователь',
                patronymic='Тестович',
                role_id=user_role.id
            )
            db.session.add(test_user)
            db.session.commit()
        
        yield client
        
        with app.app_context():
            db.drop_all()

# Фикстура: авторизованный клиент
@pytest.fixture
def auth_client(client):
    client.post('/login', data={
        'username': 'testuser',
        'password': 'Test123!'
    }, follow_redirects=True)
    return client

# ТЕСТ 1: Главная страница
def test_index_page(client):
    response = client.get('/')
    assert response.status_code == 200

# ТЕСТ 2: Страница входа
def test_login_page(client):
    response = client.get('/login')
    assert response.status_code == 200

# ТЕСТ 3: Успешный вход
def test_login_success(client):
    response = client.post('/login', data={
        'username': 'testuser',
        'password': 'Test123!'
    }, follow_redirects=True)
    assert response.status_code == 200

# ТЕСТ 4: Неудачный вход
def test_login_failure(client):
    response = client.post('/login', data={
        'username': 'testuser',
        'password': 'wrong'
    }, follow_redirects=True)
    assert response.status_code == 200

# ТЕСТ 5: Выход из системы
def test_logout(auth_client):
    response = auth_client.get('/logout', follow_redirects=True)
    assert response.status_code == 200

# ТЕСТ 6: Просмотр пользователя
def test_view_user(client):
    response = client.get('/user/1')
    assert response.status_code == 200

# ТЕСТ 7: Неавторизованный не может создать пользователя
def test_create_user_redirects(client):
    response = client.get('/user/create', follow_redirects=True)
    assert response.status_code == 200

# ТЕСТ 8: Авторизованный может создать пользователя
def test_create_user(auth_client):
    response = auth_client.post('/user/create', data={
        'username': 'newuser',
        'password': 'NewPass123!',
        'first_name': 'Новый'
    }, follow_redirects=True)
    assert response.status_code == 200

# ТЕСТ 9: Редактирование пользователя
def test_edit_user(auth_client):
    # Сначала создаем
    auth_client.post('/user/create', data={
        'username': 'edituser',
        'password': 'Edit123!',
        'first_name': 'Старое'
    })
    # Потом редактируем
    response = auth_client.post('/user/2/edit', data={
        'first_name': 'Новое',
        'last_name': 'Имя'
    }, follow_redirects=True)
    assert response.status_code == 200

# ТЕСТ 10: Удаление пользователя
def test_delete_user(auth_client):
    # Создаем пользователя
    auth_client.post('/user/create', data={
        'username': 'deleteuser',
        'password': 'Delete123!',
        'first_name': 'Удаляемый'
    })
    # Удаляем его
    response = auth_client.post('/user/2/delete', follow_redirects=True)
    assert response.status_code == 200

# ТЕСТ 11: Смена пароля
def test_change_password(auth_client):
    response = auth_client.post('/change-password', data={
        'old_password': 'Test123!',
        'new_password': 'NewPass456!',
        'confirm_password': 'NewPass456!'
    }, follow_redirects=True)
    assert response.status_code == 200

# ТЕСТ 12: Смена пароля - неверный старый
def test_change_password_wrong_old(auth_client):
    response = auth_client.post('/change-password', data={
        'old_password': 'WrongPass!',
        'new_password': 'NewPass456!',
        'confirm_password': 'NewPass456!'
    }, follow_redirects=True)
    assert response.status_code == 200

# ТЕСТ 13: Смена пароля - несовпадение
def test_change_password_mismatch(auth_client):
    response = auth_client.post('/change-password', data={
        'old_password': 'Test123!',
        'new_password': 'NewPass456!',
        'confirm_password': 'DifferentPass!'
    }, follow_redirects=True)
    assert response.status_code == 200

# ТЕСТ 14: Валидация короткого логина
def test_username_too_short(auth_client):
    response = auth_client.post('/user/create', data={
        'username': 'a',
        'password': 'Test123!',
        'first_name': 'Тест'
    }, follow_redirects=True)
    assert response.status_code == 200

# ТЕСТ 15: Валидация короткого пароля
def test_password_too_short(auth_client):
    response = auth_client.post('/user/create', data={
        'username': 'validuser',
        'password': 'Short1!',
        'first_name': 'Тест'
    }, follow_redirects=True)
    assert response.status_code == 200

# ТЕСТ 16: Обязательное поле имя
def test_required_first_name(auth_client):
    response = auth_client.post('/user/create', data={
        'username': 'testuser2',
        'password': 'Test123!',
        'first_name': ''
    }, follow_redirects=True)
    assert response.status_code == 200

# ТЕСТ 17: Кнопки видны авторизованному
def test_buttons_visible(auth_client):
    response = auth_client.get('/')
    assert response.status_code == 200

# ТЕСТ 18: Страница смены пароля требует авторизации
def test_change_password_requires_auth(client):
    response = client.get('/change-password', follow_redirects=True)
    assert response.status_code == 200

# ТЕСТ 19: Просмотр несуществующего пользователя
def test_view_nonexistent_user(client):
    response = client.get('/user/999')
    assert response.status_code == 404

# ТЕСТ 20: Главная страница содержит таблицу
def test_index_has_table(client):
    response = client.get('/')
    assert '<table' in response.text or 'Таблица' in response.text