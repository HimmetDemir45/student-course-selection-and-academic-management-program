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
5. (Istege bagli) ornek veri: `python manage.py loaddata phase4_seed` — tum seed kullanicilarinin sifresi `seedpass123` (gelistirme icin; uretimde kullanmayin).
6. `python manage.py runserver` ile projeyi baslat.

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

## Phase 4 ozeti
- Kayit kurallari: `core/services/` altinda kapasite, onkosul, zaman cakismasi, ekle-birak penceresi, durum gecisleri, GPA ve audit yardimcilari.
- Ogrenci: `/enrollments/sections/` kayit, `/students/transcript/` transkript/GPA.
- Ogretim uyesi: `/academic/instructor/enrollments/` ve not girisi.
- Giris brute-force: `LoginBruteForceMiddleware` + `accounts.login_throttle` (IP + login anahtari).

## Not
Flask iskeletinden Django mimarisine gecis surerken moduller genisletilmektedir.
