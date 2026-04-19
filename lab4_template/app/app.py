# Импорт библиотек
from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User, Role
import re

# Создаем приложение
app = Flask(__name__)
application = app

# Настройки приложения
app.config['SECRET_KEY'] = 'lab4-secret-key-change-in-production'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'  # Используем SQLite
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Инициализируем базу данных
db.init_app(app)

# Настройка Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Пожалуйста, войдите в систему для доступа к этой странице.'
login_manager.login_message_category = 'warning'

# Загрузка пользователя по ID (нужно для Flask-Login)
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Функция для проверки сложности пароля (валидация)
def validate_password(password):
    errors = []
    
    # Проверка длины
    if len(password) < 8:
        errors.append('Пароль должен содержать не менее 8 символов')
    if len(password) > 128:
        errors.append('Пароль должен содержать не более 128 символов')
    
    # Проверка на заглавную букву
    if not re.search(r'[A-ZА-Я]', password):
        errors.append('Пароль должен содержать хотя бы одну заглавную букву')
    
    # Проверка на строчную букву
    if not re.search(r'[a-zа-я]', password):
        errors.append('Пароль должен содержать хотя бы одну строчную букву')
    
    # Проверка на цифру
    if not re.search(r'\d', password):
        errors.append('Пароль должен содержать хотя бы одну цифру')
    
    # Проверка на пробелы
    if ' ' in password:
        errors.append('Пароль не должен содержать пробелов')
    
    # Проверка на допустимые символы (только буквы, цифры и спецсимволы из задания)
    allowed_chars = r'[a-zA-Zа-яА-Я0-9~!?@#$%^&*_\-+()\[\]{}><\/\\|"\'.,:;]'
    if not re.match(f'^{allowed_chars}+$', password):
        errors.append('Пароль содержит недопустимые символы')
    
    return errors

# Функция для проверки логина
def validate_username(username):
    errors = []
    
    # Проверка длины
    if len(username) < 5:
        errors.append('Логин должен содержать не менее 5 символов')
    
    # Проверка на допустимые символы (только латиница и цифры)
    if not re.match(r'^[a-zA-Z0-9]+$', username):
        errors.append('Логин может содержать только латинские буквы и цифры')
    
    # Проверка на уникальность (если передан existing_id, то проверяем что это не тот же пользователь)
    return errors

# Функция для проверки пустых полей
def validate_required_fields(data, fields):
    errors = {}
    for field in fields:
        if not data.get(field) or not data[field].strip():
            errors[field] = 'Поле не может быть пустым'
    return errors

# Главная страница - список пользователей
@app.route('/')
def index():
    # Получаем всех пользователей из базы
    users = User.query.all()
    # Для каждого пользователя получаем название роли
    users_data = []
    for idx, user in enumerate(users, start=1):
        users_data.append({
            'index': idx,
            'id': user.id,
            'full_name': user.get_full_name(),
            'role_name': user.role.name if user.role else 'Не назначена',
            'user': user
        })
    return render_template('index.html', title='Пользователи', users=users_data)

# Просмотр пользователя (доступно всем)
@app.route('/user/<int:user_id>')
def view_user(user_id):
    user = User.query.get_or_404(user_id)
    return render_template('user_view.html', title='Просмотр пользователя', user=user)

# Создание нового пользователя (только для авторизованных)
@app.route('/user/create', methods=['GET', 'POST'])
@login_required
def create_user():
    # Получаем список ролей для селектора
    roles = Role.query.all()
    
    if request.method == 'POST':
        # Получаем данные из формы
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        last_name = request.form.get('last_name', '').strip() or None
        first_name = request.form.get('first_name', '').strip()
        patronymic = request.form.get('patronymic', '').strip() or None
        role_id = request.form.get('role_id')
        role_id = int(role_id) if role_id and role_id != '' else None
        
        # Валидация данных
        has_errors = False
        field_errors = {}
        password_errors = []
        username_errors = []
        
        # Проверка обязательных полей
        required_errors = validate_required_fields(
            {'username': username, 'first_name': first_name},
            ['username', 'first_name']
        )
        if required_errors:
            has_errors = True
            field_errors.update(required_errors)
        
        # Проверка логина
        if username:
            username_errors = validate_username(username)
            # Проверка на уникальность логина
            if User.query.filter_by(username=username).first():
                username_errors.append('Пользователь с таким логином уже существует')
            if username_errors:
                has_errors = True
                field_errors['username'] = username_errors[0]
        
        # Проверка пароля
        if password:
            password_errors = validate_password(password)
            if password_errors:
                has_errors = True
                field_errors['password'] = password_errors[0]
        else:
            has_errors = True
            field_errors['password'] = 'Пароль не может быть пустым'
        
        # Если есть ошибки, показываем форму снова
        if has_errors:
            for field, error in field_errors.items():
                flash(f'{field}: {error}', 'danger')
            return render_template('user_form.html', title='Создание пользователя',
                                 user_data=request.form, roles=roles, is_edit=False)
        
        # Создаем нового пользователя
        try:
            new_user = User(
                username=username,
                password_hash=generate_password_hash(password),
                last_name=last_name,
                first_name=first_name,
                patronymic=patronymic,
                role_id=role_id
            )
            db.session.add(new_user)
            db.session.commit()
            flash(f'Пользователь {new_user.get_full_name()} успешно создан!', 'success')
            return redirect(url_for('index'))
        except Exception as e:
            db.session.rollback()
            flash(f'Ошибка при создании пользователя: {str(e)}', 'danger')
            return render_template('user_form.html', title='Создание пользователя',
                                 user_data=request.form, roles=roles, is_edit=False)
    
    # GET запрос - показываем пустую форму
    return render_template('user_form.html', title='Создание пользователя',
                         user_data={}, roles=roles, is_edit=False)

# Редактирование пользователя (только для авторизованных)
@app.route('/user/<int:user_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_user(user_id):
    user = User.query.get_or_404(user_id)
    roles = Role.query.all()
    
    if request.method == 'POST':
        # Получаем данные из формы
        last_name = request.form.get('last_name', '').strip() or None
        first_name = request.form.get('first_name', '').strip()
        patronymic = request.form.get('patronymic', '').strip() or None
        role_id = request.form.get('role_id')
        role_id = int(role_id) if role_id and role_id != '' else None
        
        # Валидация данных
        has_errors = False
        field_errors = {}
        
        # Проверка обязательных полей
        if not first_name:
            has_errors = True
            field_errors['first_name'] = 'Поле не может быть пустым'
        
        # Если есть ошибки, показываем форму снова
        if has_errors:
            for field, error in field_errors.items():
                flash(f'{field}: {error}', 'danger')
            return render_template('user_form.html', title='Редактирование пользователя',
                                 user_data={'last_name': last_name, 'first_name': first_name,
                                          'patronymic': patronymic, 'role_id': role_id},
                                 roles=roles, is_edit=True, edit_user=user)
        
        # Обновляем данные пользователя
        try:
            user.last_name = last_name
            user.first_name = first_name
            user.patronymic = patronymic
            user.role_id = role_id
            db.session.commit()
            flash(f'Данные пользователя {user.get_full_name()} успешно обновлены!', 'success')
            return redirect(url_for('index'))
        except Exception as e:
            db.session.rollback()
            flash(f'Ошибка при обновлении данных: {str(e)}', 'danger')
            return render_template('user_form.html', title='Редактирование пользователя',
                                 user_data=request.form, roles=roles, is_edit=True, edit_user=user)
    
    # GET запрос - показываем форму с данными пользователя
    user_data = {
        'last_name': user.last_name or '',
        'first_name': user.first_name,
        'patronymic': user.patronymic or '',
        'role_id': user.role_id
    }
    return render_template('user_form.html', title='Редактирование пользователя',
                         user_data=user_data, roles=roles, is_edit=True, edit_user=user)

# Удаление пользователя (только для авторизованных)
@app.route('/user/<int:user_id>/delete', methods=['POST'])
@login_required
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    
    # Нельзя удалить самого себя
    if user.id == current_user.id:
        flash('Вы не можете удалить свою собственную учетную запись!', 'danger')
        return redirect(url_for('index'))
    
    try:
        user_name = user.get_full_name()
        db.session.delete(user)
        db.session.commit()
        flash(f'Пользователь {user_name} успешно удален!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Ошибка при удалении пользователя: {str(e)}', 'danger')
    
    return redirect(url_for('index'))

# Смена пароля
@app.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    if request.method == 'POST':
        old_password = request.form.get('old_password', '')
        new_password = request.form.get('new_password', '')
        confirm_password = request.form.get('confirm_password', '')
        
        has_errors = False
        
        # Проверка старого пароля
        if not check_password_hash(current_user.password_hash, old_password):
            flash('Неверный старый пароль!', 'danger')
            has_errors = True
        
        # Проверка совпадения новых паролей
        if new_password != confirm_password:
            flash('Новый пароль и подтверждение не совпадают!', 'danger')
            has_errors = True
        
        # Валидация нового пароля
        password_errors = validate_password(new_password)
        if password_errors:
            for error in password_errors:
                flash(error, 'danger')
            has_errors = True
        
        if not has_errors:
            try:
                current_user.password_hash = generate_password_hash(new_password)
                db.session.commit()
                flash('Пароль успешно изменен!', 'success')
                return redirect(url_for('index'))
            except Exception as e:
                flash(f'Ошибка при смене пароля: {str(e)}', 'danger')
    
    return render_template('change_password.html', title='Смена пароля')

# Страница входа
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        remember = request.form.get('remember', False) == 'on'
        
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password_hash, password):
            login_user(user, remember=remember)
            flash(f'Добро пожаловать, {user.get_full_name()}!', 'success')
            next_page = request.args.get('next')
            return redirect(next_page or url_for('index'))
        else:
            flash('Неверное имя пользователя или пароль!', 'danger')
    
    return render_template('login.html', title='Вход')

# Выход из системы
@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Вы вышли из системы.', 'info')
    return redirect(url_for('index'))

# Создание таблиц при запуске
with app.app_context():
    db.create_all()

# ЗАПУСК ПРИЛОЖЕНИЯ
if __name__ == '__main__':
    app.run(debug=True)