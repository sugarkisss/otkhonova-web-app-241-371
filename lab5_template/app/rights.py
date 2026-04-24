# Модуль для проверки прав доступа
from functools import wraps
from flask import flash, redirect, url_for
from flask_login import current_user

# Словарь прав для каждой роли
ROLE_RIGHTS = {
    'admin': [
        'user.create',
        'user.edit',
        'user.view',
        'user.delete',
        'reports.view',      # просмотр журнала (все записи)
        'reports.export'     # экспорт отчётов
    ],
    'user': [
        'user.edit.self',    # редактирование своих данных
        'user.view.self',    # просмотр своего профиля
        'reports.view.self'  # просмотр только своих посещений
    ]
}

def has_right(right):
    """Проверяет, есть ли у текущего пользователя указанное право"""
    if not current_user.is_authenticated:
        return False
    
    role_name = current_user.role.name if current_user.role else None
    
    if not role_name or role_name not in ROLE_RIGHTS:
        return False
    
    allowed_rights = ROLE_RIGHTS.get(role_name, [])
    return right in allowed_rights

def check_rights(right):
    """Декоратор для проверки прав доступа"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if not has_right(right):
                flash('У вас недостаточно прав для доступа к данной странице.', 'danger')
                return redirect(url_for('index'))
            return func(*args, **kwargs)
        return wrapper
    return decorator

def can_edit_user(user):
    """Проверяет, может ли пользователь редактировать указанного"""
    if not current_user.is_authenticated:
        return False
    
    if has_right('user.edit'):  # admin
        return True
    
    if has_right('user.edit.self') and current_user.id == user.id:
        return True
    
    return False

def can_view_user(user):
    """Проверяет, может ли пользователь просматривать профиль"""
    if not current_user.is_authenticated:
        return False
    
    if has_right('user.view'):  # admin
        return True
    
    if has_right('user.view.self') and current_user.id == user.id:
        return True
    
    return False

def can_delete_user(user):
    """Проверяет, может ли пользователь удалить указанного"""
    if not current_user.is_authenticated:
        return False
    
    if has_right('user.delete'):
        return current_user.id != user.id
    
    return False