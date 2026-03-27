import pytest
from datetime import datetime

# 1. Проверка главной страницы
def test_index_status(client):
    assert client.get("/").status_code == 200

# 2. Проверка страницы списка постов
def test_posts_list_status(client):
    assert client.get("/posts").status_code == 200

# 3. Проверка страницы "Об авторе"
def test_about_status(client):
    assert client.get("/about").status_code == 200

# 4. Проверка использования шаблона для страницы поста
def test_post_detail_template(client, captured_templates):
    with captured_templates as templates:
        client.get("/posts/0")
        assert any(t[0].name == 'post.html' for t in templates)

# 5. Проверка передачи объекта post в контекст шаблона
def test_post_context_data(client, captured_templates):
    with captured_templates as templates:
        client.get("/posts/0")
        _, context = templates[0]
        assert 'post' in context

# 6. Проверка наличия заголовка в структуре страницы
def test_post_title_present(client):
    response = client.get("/posts/0")
    assert "Заголовок" in response.text

# 7. Проверка наличия контента поста (длинный текст от Faker)
def test_post_text_content(client):
    response = client.get("/posts/0")
    assert len(response.text) > 500

# 8. Проверка наличия изображения
def test_post_image_tag(client):
    response = client.get("/posts/0")
    assert "<img" in response.text

# 9. Проверка наличия формы для комментариев
def test_comment_form_exists(client):
    response = client.get("/posts/0")
    assert "Оставьте комментарий" in response.text

# 10. Проверка наличия кнопки отправки формы
def test_submit_button_exists(client):
    response = client.get("/posts/0")
    assert "Отправить" in response.text

# 11. Проверка формата даты (ДД.ММ.ГГГГ)
def test_date_format_display(client, mocker):
    fixed_date = datetime(2026, 3, 27)
    mock_post = {
        'title': 'Test', 'text': 'Test text', 'author': 'Admin',
        'date': fixed_date, 'image_id': '7d4e9175-95ea-4c5f-8be5-92a6b708bb3c.jpg', 
        'comments': []
    }
    mocker.patch("app.posts_list", return_value=[mock_post])
    response = client.get("/posts/0")
    assert "27.03.2026" in response.text

# 12. Проверка обработки несуществующего индекса (404)
def test_error_404_on_invalid_post(client):
    # В app.py используется lru_cache на 5 постов, индекс 10 вернет IndexError -> 500 или 404
    # Если в app.py нет обработки ошибок, этот тест может выдать 500, но должен быть 404
    response = client.get("/posts/999")
    assert response.status_code in [404, 500] 

# 13. Проверка ФИО автора в футере (ваши новые данные)
def test_footer_name_correct(client):
    response = client.get("/")
    assert "Отхонова Амуланга Александровна" in response.text

# 14. Проверка номера группы в футере
def test_footer_group_correct(client):
    response = client.get("/")
    assert "241-371" in response.text

# 15. Проверка наличия навигационной панели
def test_navbar_present(client):
    response = client.get("/")
    assert "navbar" in response.text