import random
from functools import lru_cache
from flask import Flask, render_template, abort # Основные инструменты Flask
from faker import Faker # Библиотека для генерации "рыбного" текста

# Инициализируем генератор случайных данных
fake = Faker()

app = Flask(__name__)
application = app # Ссылка для совместимости с хостингами

# Список ID картинок, которые лежат в папке static/images/
images_ids = [
    '7d4e9175-95ea-4c5f-8be5-92a6b708bb3c',
    '2d2ab7df-cdbc-48a8-a936-35bba702def5',
    '6e12f3de-d5fd-4ebb-855b-8cbc485278b7',
    'afc2cfe7-5cac-4b80-9b9a-d5c65ef0c728',
    'cab5b7f2-774e-4884-a200-0c0180fa777f'
]

def generate_comments(replies=True):
    """Генерирует случайные комментарии и вложенные ответы к ним."""
    comments = []
    for _ in range(random.randint(1, 3)):
        comment = {
            'author': fake.name(),
            'text': fake.text()
        }
        if replies:
            # Рекурсивно создаем ответы на комментарии
            comment['replies'] = generate_comments(replies=False)
        comments.append(comment)
    return comments

def generate_post(i):
    """Создает структуру данных для одного поста."""
    return {
        'title': f'Заголовок поста {i+1}',
        'text': fake.paragraph(nb_sentences=100),
        'author': fake.name(),
        'date': fake.date_time_between(start_date='-2y', end_date='now'),
        'image_id': f'{images_ids[i]}.jpg',
        'comments': generate_comments()
    }

@lru_cache
def posts_list():
    """
    Создает список из 5 постов. 
    Используем lru_cache, чтобы данные не менялись при каждом обновлении страницы.
    """
    posts = [generate_post(i) for i in range(5)]
    # Сортируем по дате публикации (от свежих к старым)
    return sorted(posts, key=lambda p: p['date'], reverse=True)

# --- Маршруты приложения ---

@app.route('/')
def index():
    """Главная страница с текстом задания."""
    return render_template('index.html')

@app.route('/posts')
def posts():
    """Страница со списком всех постов."""
    return render_template('posts.html', title='Посты', posts=posts_list())

@app.route('/posts/<int:index>')
def post(index):
    """
    Страница одного конкретного поста.
    index — это номер поста, который мы получаем из URL.
    """
    all_posts = posts_list()
    
    # Проверка на существование поста (нужна для тестов на ошибку 404)
    if index < 0 or index >= len(all_posts):
        abort(404)
        
    p = all_posts[index]
    # Передаем объект поста в шаблон post.html
    return render_template('post.html', title=p['title'], post=p)

@app.route('/about')
def about():
    """Страница об авторе (о тебе)."""
    return render_template('about.html', title='Об авторе')

# --- Обработка ошибок ---

@app.errorhandler(404)
def page_not_found(e):
    """
    Если мы создадим файл 404.html, Flask покажет его.
    Если файла нет, вернется стандартная ошибка, но код 404 сохранится.
    """
    # Можно просто вернуть строку или отрендерить шаблон, если он есть
    return render_template('index.html', title="404 - Не найдено"), 404

if __name__ == '__main__':
    app.run()