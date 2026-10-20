"""Monta a aplicação Flask (padrão application factory)."""
import os

from flask import Flask, render_template

from config import Config
from .extensions import csrf, db, login_manager
from .utils import formatar_data, paragrafos, linhas


def create_app(config_class=Config):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(config_class)
    os.makedirs(app.instance_path, exist_ok=True)

    if app.config.get("ATRAS_DE_PROXY"):
        # Faz o Flask saber que o visitante chegou por HTTPS (RNF07).
        from werkzeug.middleware.proxy_fix import ProxyFix
        app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)

    db.init_app(app)
    csrf.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = "admin.login"
    login_manager.login_message = "Entre com seu e-mail e senha para acessar a área administrativa."
    login_manager.login_message_category = "aviso"

    from . import models  # noqa: F401  (registra as tabelas no SQLAlchemy)
    from .controllers.admin import bp as admin_bp
    from .controllers.publico import bp as publico_bp

    app.register_blueprint(publico_bp)
    app.register_blueprint(admin_bp, url_prefix="/admin")

    app.add_template_filter(formatar_data, "data")
    app.add_template_filter(paragrafos, "paragrafos")
    app.add_template_filter(linhas, "linhas")

    _registrar_erros(app)
    _registrar_cabecalhos(app)

    from .cli import registrar_comandos
    registrar_comandos(app)

    return app


def _registrar_erros(app):
    @app.errorhandler(404)
    def nao_encontrado(erro):
        return render_template("erros/404.html"), 404

    @app.errorhandler(500)
    def erro_interno(erro):
        return render_template("erros/500.html"), 500


def _registrar_cabecalhos(app):
    @app.after_request
    def cabecalhos_de_seguranca(resposta):
        resposta.headers.setdefault("X-Content-Type-Options", "nosniff")
        resposta.headers.setdefault("X-Frame-Options", "DENY")
        resposta.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        resposta.headers.setdefault(
            "Content-Security-Policy",
            "default-src 'self'; img-src 'self' data:; style-src 'self'; "
            "script-src 'self'; frame-ancestors 'none'; form-action 'self'",
        )
        if app.config.get("SESSION_COOKIE_SECURE"):
            resposta.headers.setdefault(
                "Strict-Transport-Security", "max-age=31536000; includeSubDomains"
            )
        return resposta
