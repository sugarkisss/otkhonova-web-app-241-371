# Скрипт для заполнения БД тестовыми данными
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from models import User, Role
from werkzeug.security import generate_password_hash

print("Начинаем инициализацию базы данных...")

with app.app_context():
    # Пересоздаем таблицы
    print("Пересоздаем таблицы...")
    db.drop_all()
    db.create_all()
    print("Таблицы созданы.")
    
    # Добавляем роли
    print("Добавляем роли...")
    roles = [
        Role(name='admin', description='Администратор системы (полный доступ)'),
        Role(name='user', description='Обычный пользователь (ограниченный доступ)')
    ]
    
    for role in roles:
        db.session.add(role)
        print(f"  Добавлена роль: {role.name}")
    
    db.session.commit()
    
    # Получаем ID ролей
    admin_role = Role.query.filter_by(name='admin').first()
    user_role = Role.query.filter_by(name='user').first()
    
    # Добавляем администратора
    print("Добавляем администратора...")
    admin = User(
        username='admin',
        password_hash=generate_password_hash('Admin123!'),
        last_name='Иванов',
        first_name='Иван',
        patronymic='Иванович',
        role_id=admin_role.id
    )
    db.session.add(admin)
    print(f"  Админ: admin (пароль: Admin123!)")
    
    # Добавляем обычного пользователя
    print("Добавляем обычного пользователя...")
    user1 = User(
        username='user1',
        password_hash=generate_password_hash('User123!'),
        last_name='Петров',
        first_name='Петр',
        patronymic='Петрович',
        role_id=user_role.id
    )
    db.session.add(user1)
    print(f"  Пользователь: user1 (пароль: User123!)")
    
    # Добавляем еще одного пользователя для тестов
    user2 = User(
        username='user2',
        password_hash=generate_password_hash('User456!'),
        last_name='Сидоров',
        first_name='Сидор',
        patronymic='Сидорович',
        role_id=user_role.id
    )
    db.session.add(user2)
    print(f"  Пользователь: user2 (пароль: User456!)")
    
    db.session.commit()
    
    print("\nБаза данных успешно инициализирована!")
    print("\n=== ТЕСТОВЫЕ ДАННЫЕ ===")
    print("Роли:")
    for role in Role.query.all():
        print(f"  - {role.name}: {role.description}")
    
    print("\nПользователи:")
    for user in User.query.all():
        role_name = user.role.name if user.role else "Нет"
        print(f"  - {user.username} ({user.get_full_name()}) -> роль: {role_name}")
    
    print("\nЛогины и пароли для входа:")
    print('  Администратор: логин "admin", пароль "Admin123!"')
    print('  Обычный пользователь: логин "user1", пароль "User123!"')
    print('  Обычный пользователь: логин "user2", пароль "User456!"')