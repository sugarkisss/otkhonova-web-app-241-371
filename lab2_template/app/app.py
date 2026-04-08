from flask import Flask, render_template, request, make_response, redirect, url_for
import re

app = Flask(__name__)
application = app

def validate_phone(phone_number):
    """
    Валидация и форматирование номера телефона
    Возвращает tuple: (is_valid, formatted_number, error_message)
    """
    # Проверка на пустую строку
    if not phone_number or not phone_number.strip():
        return False, None, "Недопустимый ввод. Введите номер телефона."
    
    # ДОПОЛНИТЕЛЬНАЯ ПРОВЕРКА: номер не должен начинаться с дефиса или точки
    if phone_number.strip().startswith('-') or phone_number.strip().startswith('.'):
        return False, None, "Недопустимый ввод. В номере телефона встречаются недопустимые символы."
    
    # Проверка на недопустимые символы
    allowed_chars = set('0123456789+ ()-.')
    for char in phone_number:
        if char not in allowed_chars:
            return False, None, "Недопустимый ввод. В номере телефона встречаются недопустимые символы."
    
    # ДОПОЛНИТЕЛЬНАЯ ПРОВЕРКА: дефис не может быть первым символом
    # и не может идти подряд несколько дефисов
    if '--' in phone_number:
        return False, None, "Недопустимый ввод. В номере телефона встречаются недопустимые символы."
    
    # Извлекаем только цифры
    digits = re.sub(r'[^\d]', '', phone_number)
    
    # Проверка количества цифр
    if len(digits) == 11:
        if digits[0] not in ['7', '8']:
            return False, None, "Недопустимый ввод. Неверное количество цифр."
    elif len(digits) == 10:
        pass  # 10 цифр - допустимо
    else:
        return False, None, "Недопустимый ввод. Неверное количество цифр."
    
    # Форматирование номера
    if len(digits) == 11 and digits[0] == '7':
        digits = '8' + digits[1:]
    elif len(digits) == 10:
        digits = '8' + digits
    
    # Формат: 8-***-***-**-**
    formatted = f"{digits[0]}-{digits[1:4]}-{digits[4:7]}-{digits[7:9]}-{digits[9:11]}"
    
    return True, formatted, None

# Остальной код без изменений...
@app.route('/')
def index():
    return render_template('index.html', title='Лабораторная работа №2')

@app.route('/request-params/')
def request_params():
    params = dict(request.args)
    return render_template('request_params.html', title='Параметры URL', params=params)

@app.route('/request-headers/')
def request_headers():
    headers = dict(request.headers)
    return render_template('request_headers.html', title='Заголовки запроса', headers=headers)

@app.route('/cookies/')
def cookies():
    cookie_name = 'user_choice'
    cookie_value = request.cookies.get(cookie_name)
    
    if not cookie_value:
        resp = make_response(render_template('cookies.html', title='Cookie', 
                                             cookie_value='не установлен'))
        resp.set_cookie(cookie_name, 'example_value', max_age=3600)
        return resp
    
    return render_template('cookies.html', title='Cookie', cookie_value=cookie_value)

@app.route('/delete-cookie/')
def delete_cookie():
    resp = make_response(redirect(url_for('cookies')))
    resp.delete_cookie('user_choice')
    return resp

@app.route('/form-params/', methods=['GET', 'POST'])
def form_params():
    form_data = None
    if request.method == 'POST':
        form_data = dict(request.form)
    return render_template('form_params.html', title='Параметры формы', form_data=form_data)

@app.route('/phone-validation/', methods=['GET', 'POST'])
def phone_validation():
    formatted_phone = None
    error_message = None
    phone_number = ''
    is_invalid = False
    
    if request.method == 'POST':
        phone_number = request.form.get('phone', '')
        is_valid, formatted, error = validate_phone(phone_number)
        
        if is_valid:
            formatted_phone = formatted
        else:
            error_message = error
            is_invalid = True
    
    return render_template('phone_validation.html', 
                         title='Валидация телефона',
                         phone_number=phone_number,
                         formatted_phone=formatted_phone,
                         error_message=error_message,
                         is_invalid=is_invalid)

if __name__ == '__main__':
    app.run(debug=True)