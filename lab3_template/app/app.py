# Импортируем нужные модули из Flask
from flask import Flask, render_template, request, redirect, url_for, flash, session
# Импортируем Flask-Login для аутентификации
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user

# Создаем приложение
app = Flask(__name__)
application = app 

app.config['SECRET_KEY'] = 'my-secret-key'

# Настраиваем Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)  # Привязываем к нашему приложению
login_manager.login_view = 'login'  # Если пользователь не авторизован, отправляем на страницу login
login_manager.login_message = 'Пожалуйста, войдите в систему'  # Сообщение для неавторизованных
login_manager.login_message_category = 'warning'  # Цвет сообщения (желтый)

# Класс пользователя. UserMixin дает готовые свойства (is_authenticated и т.д.)
class User(UserMixin):
    def __init__(self, id, username, password):
        self.id = id          # Уникальный идентификатор
        self.username = username  # Логин
        self.password = password  # Пароль (в реальном проекте хранят хеш)

# База данных пользователей. Вместо БД используем словарь.
# В реальном проекте данные хранят в базе данных.
users = {
    'user': User(1, 'user', 'qwerty')  # Логин: user, пароль: qwerty
}

# Эта функция нужна Flask-Login. Она загружает пользователя по его ID.
@login_manager.user_loader
def load_user(user_id):
    # Перебираем всех пользователей в словаре
    for user in users.values():
        # Сравниваем ID (превращаем в строки, чтобы не было ошибок с типами)
        if str(user.id) == str(user_id):
            return user
    return None  # Если пользователь не найден

# СТРАНИЦА СЧЕТЧИКА ПОСЕЩЕНИЙ
@app.route('/counter/')
def counter():
    # session.get() - получаем значение из сессии. Если нет, то 0.
    visit_count = session.get('visit_count', 0)
    # Увеличиваем на 1
    visit_count += 1
    # Сохраняем обратно в сессию
    session['visit_count'] = visit_count
    # Открываем шаблон counter.html и передаем туда счетчик
    return render_template('counter.html', title='Счетчик посещений', visit_count=visit_count)

# СТРАНИЦА ВХОДА
@app.route('/login/', methods=['GET', 'POST'])  # GET - открыть страницу, POST - отправить форму
def login():
    # Если пользователь уже вошел в систему
    if current_user.is_authenticated:
        flash('Вы уже вошли в систему!', 'info')  # Показываем сообщение
        return redirect(url_for('index'))  # Отправляем на главную
    
    # Если пользователь отправил форму (POST запрос)
    if request.method == 'POST':
        # Получаем данные из формы. .strip() удаляет лишние пробелы
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        # Чекбокс "Запомнить меня". Если отмечен, то remember = True
        remember = request.form.get('remember', False) == 'on'
        
        # Ищем пользователя в нашей "базе данных"
        user = users.get(username)
        
        # Если пользователь существует И пароль правильный
        if user and user.password == password:
            # Вход выполнен. login_user - функция Flask-Login
            login_user(user, remember=remember)
            flash(f'Добро пожаловать, {username}!', 'success')  # Зеленое сообщение
            
            # Проверяем, есть ли параметр next в URL (туда хотели попасть до входа)
            next_page = request.args.get('next')
            if next_page:
                return redirect(next_page)  # Отправляем на запрошенную страницу
            return redirect(url_for('index'))  # Или на главную
        else:
            # Ошибка входа
            flash('Неверное имя пользователя или пароль!', 'danger')  # Красное сообщение
    
    # Открываем страницу с формой входа
    return render_template('login.html', title='Вход в систему')

# ВЫХОД ИЗ СИСТЕМЫ
@app.route('/logout/')
@login_required  # Только авторизованные пользователи могут выйти
def logout():
    logout_user()  # Функция Flask-Login для выхода
    flash('Вы вышли из системы.', 'info')
    return redirect(url_for('index'))

# ГЛАВНАЯ СТРАНИЦА
@app.route('/')
def index():
    return render_template('index.html', title='Главная')

# СЕКРЕТНАЯ СТРАНИЦА (только для авторизованных)
@app.route('/secret/')
@login_required  # Защита - только для вошедших пользователей
def secret():
    return render_template('secret.html', title='Секретная страница')

# ЗАПУСК ПРИЛОЖЕНИЯ (только если файл запущен напрямую)
if __name__ == '__main__':
    app.run(debug=True)  # debug=True - автоматически перезагружается при изменениях