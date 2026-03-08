from flask import Flask, render_template

from .config import DevelopmentConfig
from .extensions import bcrypt, csrf, db, login_manager, migrate
from .routes.main import main_bp


@login_manager.user_loader
def load_user(user_id: str):
    """
    Geçici user_loader implementasyonu.

    Henüz gerçek bir User modeli ve kimlik doğrulama
    akışı olmadığı için her zaman None döndürüyoruz.
    İlerleyen aşamalarda gerçek veritabanı sorgusu ile
    güncellenecek.
    """
    return None


def create_app(config_class=DevelopmentConfig) -> Flask:
    app = Flask(__name__, instance_relative_config=False)

    # Config yükleme
    app.config.from_object(config_class)

    # Eklentileri, blueprint'leri ve error handler'ları kaydet
    register_extensions(app)
    register_blueprints(app)
    register_error_handlers(app)

    return app


def register_extensions(app: Flask) -> None:
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    csrf.init_app(app)
    bcrypt.init_app(app)

    # İleride auth blueprint'i geldiğinde burası aktif kullanılacak
    login_manager.login_view = "auth.login"  # henüz yok, sadece isim rezervasyonu
    login_manager.login_message_category = "info"


def register_blueprints(app: Flask) -> None:
    # Ana sayfa / genel sayfalar
    app.register_blueprint(main_bp)


def register_error_handlers(app: Flask) -> None:
    @app.errorhandler(404)
    def not_found_error(error):  # noqa: ARG001
        return render_template("errors/404.html"), 404

    @app.errorhandler(500)
    def internal_error(error):  # noqa: ARG001
        # İleride db.session.rollback() vb. eklenebilir
        return render_template("errors/500.html"), 500