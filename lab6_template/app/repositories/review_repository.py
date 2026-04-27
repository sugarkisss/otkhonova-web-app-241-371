from app.models import Review
from sqlalchemy import desc, asc

class ReviewRepository:
    def __init__(self, db):
        self.db = db

    def get_reviews_by_course(self, course_id, sort_by='newest', page=1, per_page=10):
        """Получение отзывов для курса с пагинацией и сортировкой"""
        query = self.db.select(Review).where(Review.course_id == course_id)
        
        if sort_by == 'newest':
            query = query.order_by(desc(Review.created_at))
        elif sort_by == 'positive':
            query = query.order_by(desc(Review.rating), desc(Review.created_at))
        elif sort_by == 'negative':
            query = query.order_by(asc(Review.rating), desc(Review.created_at))
        
        return self.db.paginate(query, page=page, per_page=per_page)

    def get_recent_reviews(self, course_id, limit=5):
        """Получение последних 5 отзывов"""
        query = self.db.select(Review).where(Review.course_id == course_id).order_by(desc(Review.created_at)).limit(limit)
        return self.db.session.execute(query).scalars().all()

    def get_user_review_for_course(self, course_id, user_id):
        """Получение отзыва пользователя для курса"""
        query = self.db.select(Review).where(
            Review.course_id == course_id,
            Review.user_id == user_id
        )
        return self.db.session.execute(query).scalar_one_or_none()

    def add_review(self, course_id, user_id, rating, text):
        """Добавление нового отзыва и обновление рейтинга курса"""
        from app.models import Course
        
        review = Review(
            course_id=course_id,
            user_id=user_id,
            rating=rating,
            text=text
        )
        
        # Обновляем рейтинг курса
        course = self.db.session.get(Course, course_id)
        if course:
            course.rating_sum += rating
            course.rating_num += 1
        
        self.db.session.add(review)
        self.db.session.commit()
        return review