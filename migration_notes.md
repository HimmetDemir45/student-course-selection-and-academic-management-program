# Flask to Django Migration Notes

## 1) Flask route -> Django urls/views karsiligi
- Flask: `@blueprint.route("/path")` + function
- Django: `app/urls.py` icinde `path("path/", view_func)` + `views.py`

## 2) Flask blueprint -> Django app karsiligi
- Flask blueprint'ler moduler route gruplaridir.
- Django'da bu yapi dogrudan app seviyesinde karsilanir.
- Ornek:
  - Flask `main` blueprint -> Django `core` app
  - Flask `auth` blueprint -> Django `accounts` app

## 3) Flask config -> Django settings karsiligi
- Flask: tek `config.py` veya sinif bazli config
- Django: `config/settings/base.py`, `development.py`, `production.py`
- Ortam degiskenleri: `django-environ` ile `.env` dosyasindan okunur.

## 4) Flask extensions -> Django paket/alternatif karsiligi
- Flask-SQLAlchemy -> Django ORM (`django.db.models`)
- Flask-Migrate -> Django migration sistemi (`makemigrations`, `migrate`)
- Flask-Login -> Django auth sistemi (`django.contrib.auth`)
- Flask-WTF/CSRF -> Django form + CSRF middleware
- Flask-Bcrypt -> Django'nin built-in password hasher yapisi

## 5) Dikkat edilmesi gerekenler
- Flask'taki is mantigini bir anda tasimak yerine app bazli asamali gecis yapin.
- Once URL ve view kontratlarini tasiyin, sonra model ve servis mantigini kademeli ekleyin.
- Her tasinan modulu migration ve temel testlerle dogrulayin.
