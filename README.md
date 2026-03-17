# Student Course Selection and Academic Management Program (Django)

## Proje Ozeti
Bu repo, Flask iskeletinden Django tabanli mimariye gecirilen universite projesinin baslangic altyapisini icerir.

## Teknoloji
- Python
- Django
- MySQL
- django-environ (.env yonetimi)

## Kurulum
1. Sanal ortam olustur ve aktive et.
2. `pip install -r requirements.txt` komutunu calistir.
3. `.env.example` dosyasini `.env` olarak kopyala ve DB bilgilerini duzenle.
4. `python manage.py migrate` komutunu calistir.
5. `python manage.py runserver` ile projeyi baslat.

## Settings Yapisi
- `config/settings/base.py`
- `config/settings/development.py`
- `config/settings/production.py`

## Uygulama Modulleri
- accounts
- core
- students
- instructors
- courses
- enrollments
- academic
- dashboard
- audit_logs

## Not
Bu asama sadece iskelet kurulumudur; is kurallari ve detayli modeller sonraki asamalarda eklenecektir.
