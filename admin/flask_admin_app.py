# flask_admin_app.py
# coding: utf-8

import os
from datetime import datetime
from flask import Flask, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_admin import Admin, expose, AdminIndexView
from flask_admin.contrib.sqla import ModelView
from flask_basicauth import BasicAuth
from dotenv import load_dotenv

# 1. Загрузка .env из корня проекта
load_dotenv('/root/kuzkabuh/.env')

# 2. Конфигурация Flask
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('FLASK_DB_URI')
# Настройка BasicAuth
app.config['BASIC_AUTH_USERNAME'] = os.getenv('ADMIN_USER')
app.config['BASIC_AUTH_PASSWORD'] = os.getenv('ADMIN_PASS')
app.config['BASIC_AUTH_FORCE']    = True

# 3. Инициализация расширений
db         = SQLAlchemy(app)
basic_auth = BasicAuth(app)

# 4. Модель заявки
class Zayavka(db.Model):
    __tablename__ = 'zayavki'
    id           = db.Column(db.Integer,   primary_key=True)
    date         = db.Column(db.DateTime,  default=datetime.now, nullable=False)
    inn          = db.Column(db.String(12), nullable=False)
    email        = db.Column(db.String(120), nullable=False)
    name         = db.Column(db.String(50), nullable=False)
    phone        = db.Column(db.String(25), nullable=False)
    contact_time = db.Column(db.String(40), nullable=False)
    service      = db.Column(db.String(80), nullable=False)
    urgency      = db.Column(db.String(30), nullable=False)

# 5. Кастомный IndexView с кнопкой «Выход»
class MyAdminIndexView(AdminIndexView):
    @expose('/')
    def index(self):
        return super().index()

    @expose('/logout/')
    def logout_view(self):
        # перенаправление на /admin/ сбросит BasicAuth
        return redirect(url_for('.index'))

# 6. Кастомный ModelView для Zayavka
class ZayavkaView(ModelView):
    # Разрешаем создавать, редактировать и удалять заявки
    can_create = True
    can_edit   = True
    can_delete = True

    # Русские подписи полей
    column_labels = {
        'id':            '№',
        'date':          'Дата',
        'inn':           'ИНН',
        'email':         'Email',
        'name':          'Имя',
        'phone':         'Телефон',
        'contact_time':  'Время связи',
        'service':       'Услуга',
        'urgency':       'Система налогообложения',
    }

    # Какие столбцы показывать в списке
    column_list = ['id', 'date', 'inn', 'email', 'name', 'phone', 'contact_time', 'service', 'urgency']
    # Формы добавления/редактирования
    form_columns = ['inn', 'email', 'name', 'phone', 'contact_time', 'service', 'urgency']

# 7. Создаем и запускаем Admin
admin = Admin(
    app,
    name="BUH.KUZ’KA — Админка",
    index_view=MyAdminIndexView(url='/admin', endpoint='admin'),
    template_mode='bootstrap4'
)
admin.add_view(ZayavkaView(Zayavka, db.session, name='Заявки', endpoint='zayavki'))

# 8. Создаем таблицы, если их ещё нет
with app.app_context():
    db.create_all()

# 9. Запуск
if __name__ == '__main__':
    port = int(os.getenv('FLASK_ADMIN_PORT', 59000))
    app.run(host='0.0.0.0', port=port, debug=False)
