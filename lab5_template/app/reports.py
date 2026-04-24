# Blueprint для статистических отчётов
from flask import Blueprint, render_template, request, flash, redirect, url_for, Response
from flask_login import current_user, login_required
from models import db, VisitLog, User, Role
from rights import has_right, check_rights
from sqlalchemy import func, desc
import csv
import io

reports_bp = Blueprint('reports', __name__, url_prefix='/reports')

# Функция для записи посещения (вызывается в app.py)
def log_visit(path, user_id=None):
    """Записывает посещение страницы в журнал"""
    try:
        log = VisitLog(
            path=path,
            user_id=user_id if user_id else (current_user.id if current_user.is_authenticated else None)
        )
        db.session.add(log)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"Ошибка записи в журнал: {e}")

# Журнал посещений
@reports_bp.route('/')
@login_required
def visit_logs():
    """Страница журнала посещений (с пагинацией)"""
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    # Проверяем права
    if has_right('reports.view'):  # администратор - все записи
        logs_query = VisitLog.query.order_by(desc(VisitLog.created_at))
    elif has_right('reports.view.self'):  # обычный пользователь - только свои
        logs_query = VisitLog.query.filter_by(user_id=current_user.id).order_by(desc(VisitLog.created_at))
    else:
        flash('У вас недостаточно прав для просмотра журнала.', 'danger')
        return redirect(url_for('index'))
    
    pagination = logs_query.paginate(page=page, per_page=per_page, error_out=False)
    
    logs_data = []
    for idx, log in enumerate(pagination.items, start=(page-1)*per_page + 1):
        # Определяем имя пользователя
        if log.user:
            user_name = log.user.get_full_name() or log.user.username
        elif log.user_id:
            user_name = f'Пользователь ID:{log.user_id} (удален)'
        else:
            user_name = 'Неаутентифицированный пользователь'
        
        logs_data.append({
            'number': idx,
            'user_name': user_name,
            'path': log.path,
            'created_at': log.created_at.strftime('%d.%m.%Y %H:%M:%S')
        })
    
    return render_template('reports/visit_logs.html', title='Журнал посещений',
                         logs=logs_data, pagination=pagination, page=page)

# Отчёт по страницам
@reports_bp.route('/pages-stats')
@login_required
def pages_stats():
    """Статистика посещений по страницам"""
    if has_right('reports.view'):  # администратор - все
        stats = db.session.query(
            VisitLog.path,
            func.count(VisitLog.id).label('count')
        ).group_by(VisitLog.path).order_by(desc('count')).all()
    elif has_right('reports.view.self'):  # пользователь - только свои
        stats = db.session.query(
            VisitLog.path,
            func.count(VisitLog.id).label('count')
        ).filter_by(user_id=current_user.id).group_by(VisitLog.path).order_by(desc('count')).all()
    else:
        flash('У вас недостаточно прав для просмотра статистики.', 'danger')
        return redirect(url_for('index'))
    
    stats_data = []
    for idx, stat in enumerate(stats, start=1):
        stats_data.append({
            'number': idx,
            'path': stat.path if stat.path else '/',
            'count': stat.count
        })
    
    return render_template('reports/pages_stats.html', title='Статистика по страницам',
                         stats=stats_data)

# Экспорт отчёта по страницам
@reports_bp.route('/pages-stats/export')
@login_required
def export_pages_stats():
    """Экспорт статистики по страницам в CSV"""
    if has_right('reports.view'):
        stats = db.session.query(
            VisitLog.path,
            func.count(VisitLog.id).label('count')
        ).group_by(VisitLog.path).order_by(desc('count')).all()
    elif has_right('reports.view.self'):
        stats = db.session.query(
            VisitLog.path,
            func.count(VisitLog.id).label('count')
        ).filter_by(user_id=current_user.id).group_by(VisitLog.path).order_by(desc('count')).all()
    else:
        flash('У вас недостаточно прав для экспорта.', 'danger')
        return redirect(url_for('index'))
    
    output = io.StringIO()
    writer = csv.writer(output, delimiter=';')
    writer.writerow(['№', 'Страница', 'Количество посещений'])
    
    for idx, stat in enumerate(stats, start=1):
        path = stat.path if stat.path else '/'
        writer.writerow([idx, path, stat.count])
    
    output.seek(0)
    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={'Content-Disposition': 'attachment; filename=pages_stats.csv'}
    )

# Отчёт по пользователям
@reports_bp.route('/users-stats')
@login_required
def users_stats():
    """Статистика посещений по пользователям"""
    if has_right('reports.view'):  # администратор - по всем пользователям
        stats = db.session.query(
            User.id,
            User.last_name,
            User.first_name,
            User.patronymic,
            func.count(VisitLog.id).label('count')
        ).outerjoin(VisitLog, User.id == VisitLog.user_id).group_by(User.id).order_by(desc('count')).all()
        
        stats_data = []
        for idx, stat in enumerate(stats, start=1):
            if stat.id:
                user_name = f"{stat.last_name or ''} {stat.first_name or ''} {stat.patronymic or ''}".strip()
                if not user_name:
                    user_name = stat.id
            else:
                user_name = 'Неаутентифицированный пользователь'
            
            stats_data.append({
                'number': idx,
                'user_name': user_name,
                'count': stat.count
            })
        
        # Добавляем гостей (если есть записи без user_id)
        guest_count = VisitLog.query.filter_by(user_id=None).count()
        if guest_count > 0:
            stats_data.append({
                'number': len(stats_data) + 1,
                'user_name': 'Гость (неавторизованный)',
                'count': guest_count
            })
    
    elif has_right('reports.view.self'):  # пользователь - только свои посещения
        user_visits = VisitLog.query.filter_by(user_id=current_user.id).count()
        stats_data = [{
            'number': 1,
            'user_name': current_user.get_full_name() or current_user.username,
            'count': user_visits
        }]
    else:
        flash('У вас недостаточно прав для просмотра статистики.', 'danger')
        return redirect(url_for('index'))
    
    return render_template('reports/users_stats.html', title='Статистика по пользователям',
                         stats=stats_data)

# Экспорт отчёта по пользователям
@reports_bp.route('/users-stats/export')
@login_required
def export_users_stats():
    """Экспорт статистики по пользователям в CSV"""
    if has_right('reports.view'):
        stats = db.session.query(
            User.id,
            User.last_name,
            User.first_name,
            User.patronymic,
            func.count(VisitLog.id).label('count')
        ).outerjoin(VisitLog, User.id == VisitLog.user_id).group_by(User.id).order_by(desc('count')).all()
        
        data = []
        for stat in stats:
            if stat.id:
                user_name = f"{stat.last_name or ''} {stat.first_name or ''} {stat.patronymic or ''}".strip()
                if not user_name:
                    user_name = str(stat.id)
            else:
                user_name = 'Неаутентифицированный пользователь'
            data.append((user_name, stat.count))
        
        guest_count = VisitLog.query.filter_by(user_id=None).count()
        if guest_count > 0:
            data.append(('Гость (неавторизованный)', guest_count))
    
    elif has_right('reports.view.self'):
        user_visits = VisitLog.query.filter_by(user_id=current_user.id).count()
        data = [(current_user.get_full_name() or current_user.username, user_visits)]
    else:
        flash('У вас недостаточно прав для экспорта.', 'danger')
        return redirect(url_for('index'))
    
    output = io.StringIO()
    writer = csv.writer(output, delimiter=';')
    writer.writerow(['№', 'Пользователь', 'Количество посещений'])
    
    for idx, (user_name, count) in enumerate(data, start=1):
        writer.writerow([idx, user_name, count])
    
    output.seek(0)
    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={'Content-Disposition': 'attachment; filename=users_stats.csv'}
    )