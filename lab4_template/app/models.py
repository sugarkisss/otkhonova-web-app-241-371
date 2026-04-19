# Модели базы данных
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

# Создаем объект SQLAlchemy для работы с базой данных
db = SQLAlchemy()

# Таблица для ролей пользователей
class Role(db.Model):
    __tablename__ = 'roles'
    
    id = db.Column(db.Integer, primary_key=True)  # Уникальный идентификатор роли
    name = db.Column(db.String(50), nullable=False, unique=True)  # Название роли (например, "admin")
    description = db.Column(db.String(200))  # Описание роли
    
    # Связь с пользователями (один ко многим)
    users = db.relationship('User', back_populates='role')
    
    def __repr__(self):
        return f'<Role {self.name}>'

# Таблица для пользователей
class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)  # Уникальный идентификатор
    username = db.Column(db.String(80), unique=True, nullable=False)  # Логин (только латиница и цифры)
    password_hash = db.Column(db.String(200), nullable=False)  # Хеш пароля (не сам пароль!)
    
    last_name = db.Column(db.String(50))  # Фамилия (может быть пустой)
    first_name = db.Column(db.String(50), nullable=False)  # Имя (обязательное)
    patronymic = db.Column(db.String(50))  # Отчество (может быть пустым)
    
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'))  # Ссылка на роль (может быть пустой)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)  # Дата создания (автоматически)
    
    # Связь с ролью
    role = db.relationship('Role', back_populates='users')
    
    # Метод для получения полного ФИО
    def get_full_name(self):
        parts = [self.last_name, self.first_name, self.patronymic]
        # Убираем пустые части и объединяем через пробел
        return ' '.join([p for p in parts if p])
    
    def __repr__(self):
        return f'<User {self.username}>'