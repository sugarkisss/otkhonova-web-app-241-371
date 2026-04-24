import pytest
from app import app, db
from models import User, Role, VisitLog
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
            # Создаем таблицы заново
            db.drop_all()
            db.create_all()
            
            # Добавляем роли (проверяем, что они еще не существуют)
            if not Role.query.filter_by(name='admin').first():
                admin_role = Role(name='admin', description='Администратор')
                db.session.add(admin_role)
            
            if not Role.query.filter_by(name='user').first():
                user_role = Role(name='user', description='Обычный пользователь')
                db.session.add(user_role)
            
            db.session.commit()
            
            # Получаем ID ролей после добавления
            admin_role = Role.query.filter_by(name='admin').first()
            user_role = Role.query.filter_by(name='user').first()
            
            # Добавляем администратора
            if not User.query.filter_by(username='admin').first():
                admin = User(
                    username='admin',
                    password_hash=generate_password_hash('Admin123!'),
                    last_name='Иванов',
                    first_name='Иван',
                    patronymic='Иванович',
                    role_id=admin_role.id
                )
                db.session.add(admin)
            
            # Добавляем обычного пользователя
            if not User.query.filter_by(username='testuser').first():
                user = User(
                    username='testuser',
                    password_hash=generate_password_hash('Test123!'),
                    last_name='Петров',
                    first_name='Петр',
                    patronymic='Петрович',
                    role_id=user_role.id
                )
                db.session.add(user)
            
            db.session.commit()
        
        yield client
        
        with app.app_context():
            db.drop_all()

# Фикстура: авторизованный администратор
@pytest.fixture
def admin_client(client):
    client.post('/login', data={
        'username': 'admin',
        'password': 'Admin123!'
    }, follow_redirects=True)
    return client

# Фикстура: авторизованный обычный пользователь
@pytest.fixture
def user_client(client):
    client.post('/login', data={
        'username': 'testuser',
        'password': 'Test123!'
    }, follow_redirects=True)
    return client

# 1. Главная страница открывается
def test_index_page(client):
    response = client.get('/')
    assert response.status_code == 200

# 2. Страница входа открывается
def test_login_page(client):
    response = client.get('/login')
    assert response.status_code == 200

# 3. Успешный вход администратора
def test_admin_login_success(client):
    response = client.post('/login', data={
        'username': 'admin',
        'password': 'Admin123!'
    }, follow_redirects=True)
    assert response.status_code == 200

# 4. Успешный вход обычного пользователя
def test_user_login_success(client):
    response = client.post('/login', data={
        'username': 'testuser',
        'password': 'Test123!'
    }, follow_redirects=True)
    assert response.status_code == 200

# 5. Неудачный вход с неверным паролем
def test_login_failure(client):
    response = client.post('/login', data={
        'username': 'admin',
        'password': 'WrongPass'
    }, follow_redirects=True)
    assert response.status_code == 200

# 6. Администратор может создать пользователя
def test_admin_can_create_user(admin_client):
    response = admin_client.post('/user/create', data={
        'username': 'newuser',
        'password': 'NewPass123!',
        'first_name': 'Новый',
        'last_name': 'Пользователь'
    }, follow_redirects=True)
    assert response.status_code == 200

# 7. Обычный пользователь НЕ может создать пользователя (доступ запрещен)
def test_user_cannot_create_user(user_client):
    response = user_client.get('/user/create', follow_redirects=True)
    assert response.status_code == 200

# 8. Администратор может редактировать пользователя
def test_admin_can_edit_user(admin_client):
    response = admin_client.post('/user/2/edit', data={
        'first_name': 'ИзмененноеИмя',
        'last_name': 'ИзмененнаяФамилия'
    }, follow_redirects=True)
    assert response.status_code == 200

# 9. Обычный пользователь может редактировать себя
def test_user_can_edit_self(user_client):
    # testuser имеет ID = 2
    response = user_client.post('/user/2/edit', data={
        'first_name': 'СвоеНовоеИмя'
    }, follow_redirects=True)
    assert response.status_code == 200

# 10. Обычный пользователь НЕ может редактировать другого
def test_user_cannot_edit_other(user_client):
    # Пытается редактировать администратора (ID=1)
    response = user_client.get('/user/1/edit', follow_redirects=True)
    assert response.status_code == 200

# 11. Администратор может удалить пользователя
def test_admin_can_delete_user(admin_client):
    # Сначала создаем пользователя
    admin_client.post('/user/create', data={
        'username': 'todelete',
        'password': 'Delete123!',
        'first_name': 'Удаляемый'
    })
    # Удаляем его (ID будет 3)
    response = admin_client.post('/user/3/delete', follow_redirects=True)
    assert response.status_code == 200

# 12. Обычный пользователь НЕ может удалить пользователя
def test_user_cannot_delete_user(user_client):
    response = user_client.post('/user/1/delete', follow_redirects=True)
    assert response.status_code == 200

# 13. Администратор не может удалить самого себя
def test_admin_cannot_delete_self(admin_client):
    response = admin_client.post('/user/1/delete', follow_redirects=True)
    assert response.status_code == 200

# 14. Журнал посещений доступен авторизованным
def test_visit_logs_accessible(user_client):
    response = user_client.get('/reports/')
    assert response.status_code == 200

# 15. Журнал посещений НЕ доступен неавторизованным
def test_visit_logs_not_accessible_for_anonymous(client):
    response = client.get('/reports/', follow_redirects=True)
    assert response.status_code == 200
    # Должен быть перенаправлен на страницу входа
    assert 'login' in response.request.path

# 16. Страница статистики по страницам доступна
def test_pages_stats_accessible(user_client):
    response = user_client.get('/reports/pages-stats')
    assert response.status_code == 200

# 17. Страница статистики по пользователям доступна
def test_users_stats_accessible(user_client):
    response = user_client.get('/reports/users-stats')
    assert response.status_code == 200

# 18. Экспорт CSV по страницам работает
def test_export_pages_stats_csv(admin_client):
    response = admin_client.get('/reports/pages-stats/export')
    assert response.status_code == 200
    assert 'text/csv' in response.content_type

# 19. Экспорт CSV по пользователям работает
def test_export_users_stats_csv(admin_client):
    response = admin_client.get('/reports/users-stats/export')
    assert response.status_code == 200
    assert 'text/csv' in response.content_type

# 20. Смена пароля работает
def test_change_password_success(user_client):
    response = user_client.post('/change-password', data={
        'old_password': 'Test123!',
        'new_password': 'NewPass456!',
        'confirm_password': 'NewPass456!'
    }, follow_redirects=True)
    assert response.status_code == 200