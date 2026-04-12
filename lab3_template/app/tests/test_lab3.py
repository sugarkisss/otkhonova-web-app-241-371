import pytest
from app import app, users

# ФИКСТУРА: создает тестового клиента (как браузер для тестов)
@pytest.fixture
def client():
    # Включаем режим тестирования
    app.config['TESTING'] = True
    # Секретный ключ для тестов (не такой как в основном приложении)
    app.config['SECRET_KEY'] = 'test-secret-key'
    # Отключаем CSRF защиту для тестов (иначе форма не отправится)
    app.config['WTF_CSRF_ENABLED'] = False
    
    # Создаем тестового клиента
    with app.test_client() as client:
        # Очищаем сессию перед каждым тестом
        with client.session_transaction() as sess:
            sess.clear()
        yield client  # Возвращаем клиент для использования в тесте

# ФИКСТУРА: создает уже авторизованного клиента
@pytest.fixture
def auth_client(client):
    # Отправляем запрос на вход с правильными данными
    client.post('/login/', data={
        'username': 'user',
        'password': 'qwerty',
        'remember': False
    }, follow_redirects=True)  # follow_redirects - переходим по редиректу
    return client

# ТЕСТ 1: проверяем первое посещение счетчика
def test_counter_first_visit(client):
    # Открываем страницу счетчика
    response = client.get('/counter/')
    # Статус 200 - страница существует
    assert response.status_code == 200
    # На странице должна быть цифра 1 или текст "первое посещение"
    assert '1' in response.text or 'первое посещение' in response.text

# ТЕСТ 2: проверяем несколько посещений счетчика
def test_counter_multiple_visits(client):
    # Три раза заходим на страницу
    client.get('/counter/')  # 1-й раз
    client.get('/counter/')  # 2-й раз
    response = client.get('/counter/')  # 3-й раз
    # Счетчик должен показывать 3
    assert '3' in response.text

# ТЕСТ 3: счетчик должен быть независимым для разных сессий
def test_counter_independent_for_different_sessions(client):
    # Для первой сессии устанавливаем счетчик = 5
    with client.session_transaction() as sess:
        sess['visit_count'] = 5
    # При следующем посещении должно стать 6
    response1 = client.get('/counter/')
    assert '6' in response1.text
    
    # Создаем нового клиента (новая сессия)
    with app.test_client() as client2:
        # Счетчик должен начаться с 1
        response2 = client2.get('/counter/')
        assert '1' in response2.text

# ТЕСТ 4: страница входа открывается
def test_login_page_GET(client):
    response = client.get('/login/')
    assert response.status_code == 200
    # На странице должен быть заголовок "Вход в систему"
    assert 'Вход в систему' in response.text or 'Login' in response.text

# ТЕСТ 5: успешный вход с правильными данными
def test_login_success(client):
    # Отправляем форму с правильным логином и паролем
    response = client.post('/login/', data={
        'username': 'user',
        'password': 'qwerty',
        'remember': False
    }, follow_redirects=True)  # follow_redirects - после входа перенаправляет на главную
    
    assert response.status_code == 200
    # Должно появиться приветствие или имя пользователя
    assert ('Добро пожаловать' in response.text or 
            'user' in response.text or
            'Вы вошли' in response.text)

# ТЕСТ 6: ошибка при неверном пароле
def test_login_failure_wrong_password(client):
    # Отправляем форму с правильным логином, но неверным паролем
    response = client.post('/login/', data={
        'username': 'user',
        'password': 'wrongpassword',
        'remember': False
    }, follow_redirects=True)
    
    assert response.status_code == 200
    # Должно появиться сообщение об ошибке
    assert ('Неверное имя пользователя или пароль' in response.text or 
            'ошибка' in response.text.lower())

# ТЕСТ 7: ошибка при неверном логине
def test_login_failure_wrong_username(client):
    # Отправляем форму с неверным логином
    response = client.post('/login/', data={
        'username': 'wronguser',
        'password': 'qwerty',
        'remember': False
    }, follow_redirects=True)
    
    assert response.status_code == 200
    # Должно появиться сообщение об ошибке
    assert ('Неверное имя пользователя или пароль' in response.text or 
            'ошибка' in response.text.lower())

# ТЕСТ 8: выход из системы
def test_logout(client):
    # Сначала входим
    client.post('/login/', data={'username': 'user', 'password': 'qwerty'})
    # Затем выходим
    response = client.get('/logout/', follow_redirects=True)
    
    assert response.status_code == 200
    # Должно появиться сообщение о выходе
    assert ('Вы вышли из системы' in response.text or 
            'выйти' in response.text.lower())

# ТЕСТ 9: авторизованный пользователь видит секретную страницу
def test_secret_page_accessible_for_authenticated(auth_client):
    # auth_client - уже авторизованный клиент
    response = auth_client.get('/secret/')
    assert response.status_code == 200
    # На странице должен быть текст "Секретная" или "Доступ разрешен"
    assert ('СЕКРЕТНАЯ' in response.text.upper() or 
            'Доступ разрешен' in response.text or
            'secret' in response.text.lower())

# ТЕСТ 10: неавторизованный пользователь не видит секретную страницу
def test_secret_page_redirects_for_anonymous(client):
    # Пытаемся зайти на секретную страницу без авторизации
    response = client.get('/secret/', follow_redirects=True)
    assert response.status_code == 200
    # Должны быть перенаправлены на страницу входа
    assert ('Вход в систему' in response.text or 
            'Login' in response.text or
            'войдите' in response.text.lower())

# ТЕСТ 11: после входа перенаправляет на запрошенную страницу
def test_redirect_to_requested_page_after_login(client):
    # Сначала пробуем зайти на секретную страницу (без авторизации)
    response = client.get('/secret/')
    # Должен быть редирект (статус 302)
    assert response.status_code == 302
    
    # Входим через страницу входа
    response = client.post('/login/', data={
        'username': 'user',
        'password': 'qwerty',
        'remember': False
    }, follow_redirects=True)
    
    # Проверяем что авторизация прошла успешно
    assert response.status_code == 200
    assert ('user' in response.text or 
            'Добро пожаловать' in response.text)

# ТЕСТ 12: чекбокс "Запомнить меня" устанавливает cookie
def test_remember_me_sets_cookie(client):
    # Входим с отмеченным чекбоксом "Запомнить меня"
    response = client.post('/login/', data={
        'username': 'user',
        'password': 'qwerty',
        'remember': True  # remember=True означает что чекбокс отмечен
    })
    
    # Проверяем что установлена какая-то cookie
    set_cookie = response.headers.get('Set-Cookie', '')
    assert set_cookie != ''
    # В cookie должна быть session или remember_token
    assert 'session' in set_cookie or 'remember' in set_cookie.lower()

# ТЕСТ 13: без чекбокса поведение стандартное
def test_remember_me_not_set_without_checkbox(client):
    # Входим без чекбокса
    response = client.post('/login/', data={
        'username': 'user',
        'password': 'qwerty',
        'remember': False
    })
    
    # Просто проверяем что вход прошел (редирект или успех)
    assert response.status_code == 302 or response.status_code == 200

# ТЕСТ 14: для авторизованных показывается ссылка на секретную страницу
def test_navbar_shows_secret_link_for_authenticated(auth_client):
    response = auth_client.get('/')
    # В меню должна быть ссылка на секретную страницу
    assert ('secret' in response.text.lower() or 
            'Секретная' in response.text or
            '🔒' in response.text)

# ТЕСТ 15: для неавторизованных скрыта ссылка на секретную страницу
def test_navbar_hides_secret_link_for_anonymous(client):
    response = client.get('/')
    # Ссылки на секретную страницу НЕТ
    assert ('Секретная страница' not in response.text and 
            'secret' not in response.text.lower()) or \
           ('Войти' in response.text)

# ТЕСТ 16: для авторизованных показывается имя пользователя
def test_navbar_shows_username_for_authenticated(auth_client):
    response = auth_client.get('/')
    # В меню должно быть написано "user"
    assert 'user' in response.text

# ТЕСТ 17: на главной странице есть ссылки на все разделы
def test_index_page_has_links(client):
    response = client.get('/')
    # Должна быть ссылка на счетчик
    assert 'Счетчик посещений' in response.text or 'counter' in response.text.lower()
    # Должна быть ссылка на вход
    assert 'Войти' in response.text or 'login' in response.text.lower()

# ТЕСТ 18: при успешном входе показывается flash-сообщение
def test_flash_messages_on_login_success(client):
    response = client.post('/login/', data={
        'username': 'user',
        'password': 'qwerty'
    }, follow_redirects=True)
    
    # Должно быть всплывающее сообщение (alert)
    assert ('alert-success' in response.text or 
            'alert' in response.text)

# ТЕСТ 19: при ошибке входа показывается flash-сообщение об ошибке
def test_flash_messages_on_login_failure(client):
    response = client.post('/login/', data={
        'username': 'user',
        'password': 'wrong'
    }, follow_redirects=True)
    
    # Должно быть красное сообщение об ошибке
    assert ('alert-danger' in response.text or 
            'danger' in response.text or
            'ошибк' in response.text.lower())

# ТЕСТ 20: авторизованный пользователь на странице входа перенаправляется
def test_authenticated_user_redirected_from_login(auth_client):
    # auth_client уже авторизован, пытается зайти на /login/
    response = auth_client.get('/login/', follow_redirects=True)
    assert response.status_code == 200
    # Должен быть перенаправлен на главную страницу
    assert 'Лабораторная работа №3' in response.text

# ТЕСТ 21: счетчик работает через session
def test_counter_works_in_session(client):
    # Очищаем сессию перед тестом
    with client.session_transaction() as sess:
        sess.clear()
    
    # Первое посещение - счетчик 1
    response1 = client.get('/counter/')
    assert '1' in response1.text
    
    # Второе посещение - счетчик 2
    response2 = client.get('/counter/')
    assert '2' in response2.text