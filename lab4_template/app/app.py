# Импорт библиотек
from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User, Role

import re
# re - регулярные выражения, нужны для проверки пароля и логина

# Создаем приложение
app = Flask(__name__)
application = app  # Это для хостинга

# Настройки приложения
app.config['SECRET_KEY'] = 'lab4-secret-key-change-in-production'
# Секретный ключ нужен для сессий и защиты. В реальном проекте его прячут.

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'  # Используем SQLite
# Это путь к файлу базы данных. users.db создастся в папке с проектом.

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
# Отключаем слежение за изменениями (для производительности)

# Инициализируем базу данных (связываем приложение с БД)
db.init_app(app)

# Настройка Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)  # Привязываем к нашему приложению
login_manager.login_view = 'login'  # Если пользователь не авторизован, отправляем на страницу login
login_manager.login_message = 'Пожалуйста, войдите в систему для доступа к этой странице.'
login_manager.login_message_category = 'warning'  # Желтое сообщение

# Загрузка пользователя по ID (нужно для Flask-Login)
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
    # User.query.get - ищем пользователя в базе по ID

# Функция для проверки сложности пароля (валидация)
def validate_password(password):
    errors = []  # Список ошибок, который будем возвращать
    
    # Проверка длины
    if len(password) < 8:
        errors.append('Пароль должен содержать не менее 8 символов')
    if len(password) > 128:
        errors.append('Пароль должен содержать не более 128 символов')
    
    # Проверка на заглавную букву (латиница или кириллица)
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
    
    # Проверка на допустимые символы (буквы, цифры и спецсимволы из задания)
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
    
    return errors

# Функция для проверки обязательных полей (не могут быть пустыми)
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
    
    # Для каждого пользователя формируем данные для таблицы
    users_data = []
    for idx, user in enumerate(users, start=1):  # start=1 - нумерация с 1
        users_data.append({
            'index': idx,  # Порядковый номер
            'id': user.id,  # ID из базы
            'full_name': user.get_full_name(),  # ФИО (метод из модели User)
            'role_name': user.role.name if user.role else 'Не назначена',  # Название роли
            'user': user  # Сам объект пользователя (на всякий случай)
        })
    return render_template('index.html', title='Пользователи', users=users_data)

# Просмотр пользователя (доступно всем, даже без авторизации)
@app.route('/user/<int:user_id>')
def view_user(user_id):
    # get_or_404 - ищем пользователя, если нет - ошибка 404
    user = User.query.get_or_404(user_id)
    return render_template('user_view.html', title='Просмотр пользователя', user=user)

# Создание нового пользователя (только для авторизованных)
@app.route('/user/create', methods=['GET', 'POST'])
@login_required  # Декоратор - требует авторизации
def create_user():
    # Получаем список ролей для выпадающего списка (селектора)
    roles = Role.query.all()
    
    if request.method == 'POST':  # Если пользователь отправил форму
        # Получаем данные из формы
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        last_name = request.form.get('last_name', '').strip() or None  # Если пусто - None
        first_name = request.form.get('first_name', '').strip()
        patronymic = request.form.get('patronymic', '').strip() or None
        role_id = request.form.get('role_id')
        role_id = int(role_id) if role_id and role_id != '' else None
        
        # Валидация данных (проверка на ошибки)
        has_errors = False
        field_errors = {}
        
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
                field_errors['username'] = username_errors[0]  # Берем первую ошибку
        
        # Проверка пароля
        if password:
            password_errors = validate_password(password)
            if password_errors:
                has_errors = True
                field_errors['password'] = password_errors[0]
        else:
            has_errors = True
            field_errors['password'] = 'Пароль не может быть пустым'
        
        # Если есть ошибки, показываем форму снова с сообщениями
        if has_errors:
            for field, error in field_errors.items():
                flash(f'{field}: {error}', 'danger')  # Красное сообщение об ошибке
            return render_template('user_form.html', title='Создание пользователя',
                                 user_data=request.form, roles=roles, is_edit=False)
        
        # Если ошибок нет - создаем пользователя
        try:
            new_user = User(
                username=username,
                password_hash=generate_password_hash(password),  # Хешируем пароль!
                last_name=last_name,
                first_name=first_name,
                patronymic=patronymic,
                role_id=role_id
            )
            db.session.add(new_user)  # Добавляем в сессию БД
            db.session.commit()  # Сохраняем в базу
            flash(f'Пользователь {new_user.get_full_name()} успешно создан!', 'success')
            return redirect(url_for('index'))  # Перенаправляем на список пользователей
        except Exception as e:
            db.session.rollback()  # Откатываем изменения при ошибке
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
    user = User.query.get_or_404(user_id)  # Находим пользователя
    roles = Role.query.all()  # Список ролей для селектора
    
    if request.method == 'POST':
        # Получаем данные из формы (логин и пароль не меняем!)
        last_name = request.form.get('last_name', '').strip() or None
        first_name = request.form.get('first_name', '').strip()
        patronymic = request.form.get('patronymic', '').strip() or None
        role_id = request.form.get('role_id')
        role_id = int(role_id) if role_id and role_id != '' else None
        
        # Валидация - проверяем только имя (обязательное поле)
        has_errors = False
        field_errors = {}
        
        if not first_name:
            has_errors = True
            field_errors['first_name'] = 'Поле не может быть пустым'
        
        # Если есть ошибки
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
    
    # GET запрос - показываем форму с текущими данными пользователя
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
    
    # Нельзя удалить самого себя (чтобы не остаться без админа)
    if user.id == current_user.id:
        flash('Вы не можете удалить свою собственную учетную запись!', 'danger')
        return redirect(url_for('index'))
    
    try:
        user_name = user.get_full_name()
        db.session.delete(user)  # Удаляем из сессии
        db.session.commit()  # Сохраняем изменения
        flash(f'Пользователь {user_name} успешно удален!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Ошибка при удалении пользователя: {str(e)}', 'danger')
    
    return redirect(url_for('index'))

# Смена пароля текущего пользователя
@app.route('/change-password', methods=['GET', 'POST'])
@login_required  # Только для авторизованных
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
        
        # Если ошибок нет - меняем пароль
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
    # Если пользователь уже вошел, отправляем на главную
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        remember = request.form.get('remember', False) == 'on'  # Чекбокс "Запомнить меня"
        
        # Ищем пользователя в базе
        user = User.query.filter_by(username=username).first()
        
        # Проверяем пароль (сравниваем хеш)
        if user and check_password_hash(user.password_hash, password):
            login_user(user, remember=remember)  # Вход выполнен
            flash(f'Добро пожаловать, {user.get_full_name()}!', 'success')
            next_page = request.args.get('next')  # Куда хотели попасть до входа
            return redirect(next_page or url_for('index'))
        else:
            flash('Неверное имя пользователя или пароль!', 'danger')
    
    return render_template('login.html', title='Вход')

# Выход из системы
@app.route('/logout')
@login_required
def logout():
    logout_user()  # Функция Flask-Login для выхода
    flash('Вы вышли из системы.', 'info')
    return redirect(url_for('index'))

# Создание таблиц при запуске (если их нет)
with app.app_context():
    db.create_all()

# Запуск приложения (только если файл запущен напрямую)
if __name__ == '__main__':
    app.run(debug=True)  # debug=True - авто перезагрузка при изменениях