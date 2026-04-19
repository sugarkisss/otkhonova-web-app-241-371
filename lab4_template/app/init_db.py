# Скрипт для заполнения БД тестовыми данными
from app import app, db
from models import User, Role
from werkzeug.security import generate_password_hash

# Создаем контекст приложения (нужно для работы с БД вне запроса)
with app.app_context():
    # Создаем таблицы (если их нет)
    db.create_all()
    
    # Добавляем роли
    roles = [
        Role(name='admin', description='Администратор системы'),
        Role(name='user', description='Обычный пользователь'),
        Role(name='manager', description='Менеджер')
    ]
    
    # Добавляем каждую роль, если ее еще нет
    for role in roles:
        if not Role.query.filter_by(name=role.name).first():
            db.session.add(role)
    
    db.session.commit()  # Сохраняем роли
    
    # Добавляем тестового пользователя admin
    if not User.query.filter_by(username='admin').first():
        admin = User(
            username='admin',
            password_hash=generate_password_hash('Admin123!'),  # Хешируем пароль
            last_name='Иванов',
            first_name='Иван',
            patronymic='Иванович',
            role_id=Role.query.filter_by(name='admin').first().id
        )
        db.session.add(admin)
    
    # Добавляем тестового пользователя user1
    if not User.query.filter_by(username='user1').first():
        user1 = User(
            username='user1',
            password_hash=generate_password_hash('User123!'),
            last_name='Петров',
            first_name='Петр',
            patronymic='Петрович',
            role_id=Role.query.filter_by(name='user').first().id
        )
        db.session.add(user1)
    
    db.session.commit()  # Сохраняем пользователей
    
    print('База данных успешно инициализирована!')
    print('Тестовые пользователи:')
    print('  Логин: admin, пароль: Admin123!')
    print('  Логин: user1, пароль: User123!')