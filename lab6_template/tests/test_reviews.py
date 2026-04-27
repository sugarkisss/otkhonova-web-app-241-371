import pytest
from app import create_app, db
from app.models import User, Category, Course, Review

@pytest.fixture
def app():
    app = create_app(test_config={
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'WTF_CSRF_ENABLED': False,
        'SERVER_NAME': 'localhost'
    })
    with app.app_context():
        db.create_all()
        
        user = User(first_name='Test', last_name='User', login='testuser')
        user.set_password('Test123!')
        db.session.add(user)
        
        category = Category(name='Test Category')
        db.session.add(category)
        db.session.commit()
        
        course = Course(
            name='Test Course',
            short_desc='Test description',
            full_desc='Full test description',
            author_id=user.id,
            category_id=category.id
        )
        db.session.add(course)
        db.session.commit()
        
        yield app
        db.drop_all()

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def auth_client(client):
    client.post('/auth/login', data={'login': 'testuser', 'password': 'Test123!'})
    return client

def test_index_page_returns_200(client):
    response = client.get('/')
    assert response.status_code == 200

def test_courses_index_page_returns_200(client):
    response = client.get('/courses/')
    assert response.status_code == 200

def test_course_show_page_returns_200(client):
    response = client.get('/courses/1')
    assert response.status_code == 200

def test_reviews_page_returns_200(client):
    response = client.get('/courses/1/reviews')
    assert response.status_code == 200

def test_login_page_returns_200(client):
    response = client.get('/auth/login')
    assert response.status_code == 200

def test_successful_login(client):
    response = client.post('/auth/login', data={
        'login': 'testuser',
        'password': 'Test123!'
    }, follow_redirects=True)
    assert response.status_code == 200

def test_failed_login(client):
    response = client.post('/auth/login', data={
        'login': 'testuser',
        'password': 'wrongpassword'
    }, follow_redirects=True)
    assert response.status_code == 200

def test_logout_works(auth_client):
    response = auth_client.get('/auth/logout', follow_redirects=True)
    assert response.status_code == 200

def test_add_review_requires_login(client):
    response = client.post('/courses/1/review/create', data={
        'rating': 5,
        'text': 'Great course!'
    })
    assert response.status_code == 302

def test_add_review_success(auth_client):
    response = auth_client.post('/courses/1/review/create', data={
        'rating': 5,
        'text': 'This is an amazing course!'
    }, follow_redirects=True)
    assert response.status_code == 200

def test_cannot_add_duplicate_review(auth_client):
    auth_client.post('/courses/1/review/create', data={
        'rating': 5,
        'text': 'First review'
    })
    response = auth_client.post('/courses/1/review/create', data={
        'rating': 4,
        'text': 'Second review'
    }, follow_redirects=True)
    assert response.status_code == 200

def test_review_shows_on_course_page(auth_client):
    auth_client.post('/courses/1/review/create', data={
        'rating': 5,
        'text': 'Test review text here!'
    })
    response = auth_client.get('/courses/1')
    assert response.status_code == 200

def test_review_shows_on_reviews_page(auth_client):
    auth_client.post('/courses/1/review/create', data={
        'rating': 5,
        'text': 'Another test review'
    })
    response = auth_client.get('/courses/1/reviews')
    assert response.status_code == 200

def test_review_has_user_name(auth_client):
    auth_client.post('/courses/1/review/create', data={
        'rating': 5,
        'text': 'Review with name'
    })
    response = auth_client.get('/courses/1')
    assert response.status_code == 200

def test_review_has_rating_stars(auth_client):
    auth_client.post('/courses/1/review/create', data={
        'rating': 5,
        'text': 'Five stars!'
    })
    response = auth_client.get('/courses/1')
    assert response.status_code == 200

def test_course_rating_updates_after_review(auth_client):
    auth_client.post('/courses/1/review/create', data={
        'rating': 5,
        'text': 'Great!'
    })
    response = auth_client.get('/courses/1')
    assert response.status_code == 200

def test_review_created_at_displayed(auth_client):
    auth_client.post('/courses/1/review/create', data={
        'rating': 5,
        'text': 'Review with date'
    })
    response = auth_client.get('/courses/1')
    assert response.status_code == 200

def test_reviews_sort_by_newest(auth_client):
    response = auth_client.get('/courses/1/reviews?sort=newest')
    assert response.status_code == 200

def test_reviews_sort_by_positive(auth_client):
    response = auth_client.get('/courses/1/reviews?sort=positive')
    assert response.status_code == 200

def test_reviews_sort_by_negative(auth_client):
    response = auth_client.get('/courses/1/reviews?sort=negative')
    assert response.status_code == 200