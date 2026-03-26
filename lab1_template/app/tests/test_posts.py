import pytest
from datetime import datetime
from app import app as application

def test_posts_index(client):
    response = client.get("/posts")
    assert response.status_code == 200
    assert "Последние посты" in response.text

def test_posts_index_template(client, captured_templates, mocker, posts_list):
    with captured_templates as templates:
        mocker.patch(
            "app.posts_list",
            return_value=posts_list,
            autospec=True
        )
        
        _ = client.get('/posts')
        assert len(templates) == 1
        template, context = templates[0]
        assert template.name == 'posts.html'
        assert context['title'] == 'Посты'
        assert len(context['posts']) == 1

def test_post_page_status(client, mocker, posts_list):
    mocker.patch("app.posts_list", return_value=posts_list, autospec=True)
    response = client.get("/posts/0")
    assert response.status_code == 200

def test_post_page_not_found(client, mocker, posts_list):
    mocker.patch("app.posts_list", return_value=posts_list, autospec=True)
    response = client.get("/posts/99")
    assert response.status_code == 404

def test_post_page_negative_index(client, mocker, posts_list):
    mocker.patch("app.posts_list", return_value=posts_list, autospec=True)
    response = client.get("/posts/-1")
    assert response.status_code == 404

def test_post_page_template(client, captured_templates, mocker, posts_list):
    with captured_templates as templates:
        mocker.patch("app.posts_list", return_value=posts_list, autospec=True)
        
        _ = client.get('/posts/0')
        assert len(templates) == 1
        template, context = templates[0]
        assert template.name == 'post.html'
        assert context['title'] == posts_list[0]['title']
        assert context['post'] == posts_list[0]

def test_post_page_contains_title(client, mocker, posts_list):
    mocker.patch("app.posts_list", return_value=posts_list, autospec=True)
    response = client.get("/posts/0")
    assert posts_list[0]['title'] in response.text

def test_post_page_contains_author(client, mocker, posts_list):
    mocker.patch("app.posts_list", return_value=posts_list, autospec=True)
    response = client.get("/posts/0")
    assert posts_list[0]['author'] in response.text

def test_post_page_contains_text(client, mocker, posts_list):
    mocker.patch("app.posts_list", return_value=posts_list, autospec=True)
    response = client.get("/posts/0")
    assert posts_list[0]['text'] in response.text

def test_post_page_date_format(client, mocker, posts_list):
    mocker.patch("app.posts_list", return_value=posts_list, autospec=True)
    response = client.get("/posts/0")
    expected_date = posts_list[0]['date'].strftime('%d.%m.%Y')
    assert expected_date in response.text

def test_post_page_contains_image(client, mocker, posts_list):
    mocker.patch("app.posts_list", return_value=posts_list, autospec=True)
    response = client.get("/posts/0")
    assert posts_list[0]['image_id'] in response.text

def test_post_page_contains_comment_form(client, mocker, posts_list):
    mocker.patch("app.posts_list", return_value=posts_list, autospec=True)
    response = client.get("/posts/0")
    assert "Оставьте комментарий" in response.text
    assert "Отправить" in response.text
    assert 'textarea' in response.text

def test_post_page_contains_comments_section(client, mocker, posts_list):
    posts_list[0]['comments'] = [
        {'author': 'Test Author', 'text': 'Test comment', 'replies': []}
    ]
    mocker.patch("app.posts_list", return_value=posts_list, autospec=True)
    response = client.get("/posts/0")
    assert "Комментарии" in response.text
    assert "Test Author" in response.text
    assert "Test comment" in response.text

def test_post_page_contains_replies(client, mocker, posts_list):
    posts_list[0]['comments'] = [
        {'author': 'Test Author', 'text': 'Test comment', 
         'replies': [{'author': 'Reply Author', 'text': 'Reply text'}]}
    ]
    mocker.patch("app.posts_list", return_value=posts_list, autospec=True)
    response = client.get("/posts/0")
    assert "Reply Author" in response.text
    assert "Reply text" in response.text

def test_index_page(client):
    response = client.get("/")
    assert response.status_code == 200
    assert "Задание к лабораторной работе" in response.text

def test_about_page(client):
    response = client.get("/about")
    assert response.status_code == 200
    assert "Об авторе" in response.text

def test_footer_in_base_template(client):
    response = client.get("/")
    assert "Иванов Иван Иванович" in response.text
    assert "Группа: ИТ-21" in response.text

def test_404_template_exists(client):
    response = client.get("/nonexistent")
    assert response.status_code == 404
    assert "Страница не найдена" in response.text or "404" in response.text

def test_post_page_multiple_posts(client, mocker):
    multiple_posts = [
        {'title': 'Post 1', 'text': 'Text 1', 'author': 'Author 1', 
         'date': datetime(2025, 3, 10), 'image_id': '1.jpg', 'comments': []},
        {'title': 'Post 2', 'text': 'Text 2', 'author': 'Author 2', 
         'date': datetime(2025, 3, 11), 'image_id': '2.jpg', 'comments': []}
    ]
    mocker.patch("app.posts_list", return_value=multiple_posts, autospec=True)
    
    response1 = client.get("/posts/0")
    assert "Post 1" in response1.text
    assert "Author 1" in response1.text
    
    response2 = client.get("/posts/1")
    assert "Post 2" in response2.text
    assert "Author 2" in response2.text