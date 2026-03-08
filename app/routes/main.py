from flask import Blueprint, render_template

main_bp = Blueprint("main", __name__)


@main_bp.get("/")
def index():
    # İleride dashboard veya landing page'e evrilebilir
    return render_template("home/index.html", title="Ana Sayfa")