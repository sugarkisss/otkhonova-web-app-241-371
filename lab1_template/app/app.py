import random
from functools import lru_cache
from flask import Flask, render_template, abort  # Импортируем Flask и вспомогательные функции
from faker import Faker  # Библиотека для генерации случайных данных (имена, тексты, даты)

# Инициализируем объект Faker с русским языком (по желанию можно добавить locale='ru_RU')
fake = Faker()

# Создаем само веб-приложение Flask
app = Flask(__name__)
application = app  # Это нужно для совместимости с некоторыми хостингами (например, PythonAnywhere)

# Список ID изображений, которые лежат в папке static/images
# Flask будет подставлять эти строки в теги <img src="...">
images_ids = [
    '7d4e9175-95ea-4c5f-8be5-92a6b708bb3c',
    '2d2ab7df-cdbc-48a8-a936-35bba702def5',
    '6e12f3de-d5fd-4ebb-855b-8cbc485278b7',
    'afc2cfe7-5cac-4b80-9b9a-d5c65ef0c728',
    'cab5b7f2-774e-4884-a200-0c0180fa777f'
]

def generate_comments(replies=True):
    """
    Вспомогательная функция для создания списка случайных комментариев.
    Если replies=True, то функция вызывает сама себя для создания ответов на комментарии.
    """
    comments = []
    # Генерируем от 1 до 3 комментариев
    for _ in range(random.randint(1, 3)):
        comment = {
            'author': fake.name(),  # Случайное имя автора
            'text': fake.text()     # Случайный текст комментария
        }
        # Если это основной комментарий, добавим к нему вложенные ответы
        if replies:
            comment['replies'] = generate_comments(replies=False)
        comments.append(comment)
    return comments

def generate_post(i):
    """
    Функция создает словарь с данными для одного поста.
    i - это индекс (номер) картинки из списка images_ids.
    """
    return {
        'title': f'Заголовок поста {i+1}', # Формируем название
        'text': fake.paragraph(nb_sentences=100), # Генерируем длинный текст поста
        'author': fake.name(), # Случайное имя автора поста
        'date': fake.date_time_between(start_date='-2y', end_date='now'), # Дата за последние 2 года
        'image_id': f'{images_ids[i]}.jpg', # Название файла картинки
        'comments': generate_comments() # Создаем список комментариев для этого поста
    }

@lru_cache
def posts_list():
    """
    Создает список из 5 постов и кэширует его.
    @lru_cache нужен, чтобы при каждом обновлении страницы посты не менялись на новые.
    Сортируем посты по дате (от новых к старым).
    """
    posts = [generate_post(i) for i in range(5)]
    return sorted(posts, key=lambda p: p['date'], reverse=True)

# --- МАРШРУТЫ (ROUTES) ---

@app.route('/')
def index():
    """Главная страница. Просто отображает файл index.html."""
    return render_template('index.html')

@app.route('/posts')
def posts():
    """
    Страница со списком всех постов.
    Передает список всех постов (posts_list()) в шаблон posts.html под именем 'posts'.
    """
    return render_template('posts.html', title='Посты', posts=posts_list())

@app.route('/posts/<int:index>')
def post(index):
    """
    Страница конкретного поста. 
    Принимает из URL число (index), например: /posts/0
    """
    all_posts = posts_list() # Получаем список всех постов
    
    # Проверка: если номер поста меньше 0 или больше, чем у нас есть в списке
    if index < 0 or index >= len(all_posts):
        abort(404) # Прерываем работу и выдаем ошибку 404 (Not Found)
    
    # Берем нужный пост по его индексу
    current_post = all_posts[index]
    
    # Отправляем данные в шаблон post.html.
    # В шаблоне мы сможем обращаться к переменной 'post', чтобы вывести заголовок, текст и т.д.
    return render_template('post.html', title=current_post['title'], post=current_post)

@app.route('/about')
def about():
    """Страница об авторе."""
    return render_template('about.html', title='Об авторе')

# Точка входа: если файл запущен напрямую, запускаем сервер Flask
if __name__ == '__main__':
    app.run()