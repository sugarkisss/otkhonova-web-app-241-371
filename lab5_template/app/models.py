# Модели базы данных
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

# Создаем объект SQLAlchemy для работы с базой данных
db = SQLAlchemy()

# Таблица для ролей пользователей
class Role(db.Model):
    __tablename__ = 'roles'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False, unique=True)
    description = db.Column(db.String(200))
    
    # Связь с пользователями (один ко многим)
    users = db.relationship('User', back_populates='role')
    
    def __repr__(self):
        return f'<Role {self.name}>'

# Таблица для пользователей
class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    
    last_name = db.Column(db.String(50))
    first_name = db.Column(db.String(50), nullable=False)
    patronymic = db.Column(db.String(50))
    
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    role = db.relationship('Role', back_populates='users')
    
    def get_full_name(self):
        parts = [self.last_name, self.first_name, self.patronymic]
        return ' '.join([p for p in parts if p])
    
    def __repr__(self):
        return f'<User {self.username}>'

# Новая таблица: Журнал посещений (для ЛР5)
class VisitLog(db.Model):
    __tablename__ = 'visit_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    path = db.Column(db.String(200), nullable=False)  # Путь до страницы
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)  # Может быть NULL для гостей
    created_at = db.Column(db.DateTime, default=datetime.utcnow)  # Дата посещения
    
    # Связь с пользователем
    user = db.relationship('User', foreign_keys=[user_id])
    
    def __repr__(self):
        return f'<VisitLog {self.path} by {self.user_id}>'