from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user

app = Flask(__name__)
application = app

app.config['SECRET_KEY'] = 'ecret-key-here'

# НАСТРОЙКА FLASK-LOGIN

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Пожалуйста, войдите в систему для доступа к этой странице.'
login_manager.login_message_category = 'warning'

# КЛАСС ПОЛЬЗОВАТЕЛЯ

class User(UserMixin):
    def __init__(self, id, username, password):
        self.id = id
        self.username = username
        self.password = password

users = {
    'user': User(1, 'user', 'qwerty')
}

@login_manager.user_loader
def load_user(user_id):
    for user in users.values():
        if str(user.id) == str(user_id):
            return user
    return None

# СЧЕТЧИК ПОСЕЩЕНИЙ

@app.route('/counter/')
def counter():
    visit_count = session.get('visit_count', 0)
    visit_count += 1
    session['visit_count'] = visit_count
    return render_template('counter.html', title='Счетчик посещений', visit_count=visit_count)

# СТРАНИЦА ВХОДА

@app.route('/login/', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        flash('Вы уже вошли в систему!', 'info')
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        remember = request.form.get('remember', False) == 'on'
        
        user = users.get(username)
        
        if user and user.password == password:
            login_user(user, remember=remember)
            flash(f'Добро пожаловать, {username}!', 'success')
            
            next_page = request.args.get('next')
            if next_page:
                return redirect(next_page)
            return redirect(url_for('index'))
        else:
            flash('Неверное имя пользователя или пароль!', 'danger')
    
    return render_template('login.html', title='Вход в систему')

# ВЫХОД ИЗ СИСТЕМЫ

@app.route('/logout/')
@login_required
def logout():
    logout_user()
    flash('Вы вышли из системы.', 'info')
    return redirect(url_for('index'))

# ГЛАВНАЯ СТРАНИЦА

@app.route('/')
def index():
    return render_template('index.html', title='Главная')

# СЕКРЕТНАЯ СТРАНИЦА

@app.route('/secret/')
@login_required
def secret():
    return render_template('secret.html', title='Секретная страница')

# ЗАПУСК

if __name__ == '__main__':
    app.run(debug=True)