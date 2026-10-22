"""Monta a aplicação Flask (padrão application factory)."""
import logging
import os

from flask import Flask, jsonify, render_template, request
from flask.logging import default_handler

from config import Config
from .extensions import csrf, db, limiter, login_manager, migrate
from .utils import formatar_data, paragrafos, linhas

PASTA_MIGRACOES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "migrations")


def create_app(config_class=Config):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(config_class)
    os.makedirs(app.instance_path, exist_ok=True)
    _configurar_logs(app)

    if app.config.get("ATRAS_DE_PROXY"):
        # Faz o Flask saber que o visitante chegou por HTTPS (RNF07) e qual é o
        # IP real, usado no limite de tentativas.
        from werkzeug.middleware.proxy_fix import ProxyFix
        app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)

    db.init_app(app)
    migrate.init_app(app, db, directory=PASTA_MIGRACOES, render_as_batch=True)
    csrf.init_app(app)
    limiter.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = "admin.login"
    login_manager.login_message = "Entre com seu e-mail e senha para acessar a área administrativa."
    login_manager.login_message_category = "aviso"

    from . import models  # noqa: F401  (registra as tabelas no SQLAlchemy)
    from .controllers.admin import bp as admin_bp
    from .controllers.api import bp as api_bp
    from .controllers.publico import bp as publico_bp

    app.register_blueprint(publico_bp)
    app.register_blueprint(admin_bp, url_prefix="/admin")
    app.register_blueprint(api_bp, url_prefix="/api/v1")

    app.add_template_filter(formatar_data, "data")
    app.add_template_filter(paragrafos, "paragrafos")
    app.add_template_filter(linhas, "linhas")

    _registrar_erros(app)
    _registrar_cabecalhos(app)

    from .cli import registrar_comandos
    registrar_comandos(app)

    return app


def _configurar_logs(app):
    """Registros no terminal (no Render, aparecem na aba Logs).

    Não registra dados de visitantes (RNF10): só ações da área administrativa
    e erros do sistema.
    """
    default_handler.setFormatter(
        logging.Formatter("%(asctime)s %(levelname)s [%(name)s] %(message)s")
    )
    app.logger.setLevel(app.config.get("NIVEL_LOG", "INFO"))


def _eh_api():
    return request.path.startswith("/api/")


def _registrar_erros(app):
    @app.errorhandler(404)
    def nao_encontrado(erro):
        if _eh_api():
            return jsonify(erro="Não encontrado."), 404
        return render_template("erros/404.html"), 404

    @app.errorhandler(429)
    def muitas_tentativas(erro):
        if _eh_api():
            return jsonify(erro="Muitas requisições. Tente de novo em alguns minutos."), 429
        return render_template("erros/429.html"), 429

    @app.errorhandler(500)
    def erro_interno(erro):
        app.logger.error("Erro 500 em %s", request.path)
        if _eh_api():
            return jsonify(erro="Erro no servidor."), 500
        return render_template("erros/500.html"), 500


def _registrar_cabecalhos(app):
    @app.after_request
    def cabecalhos_de_seguranca(resposta):
        resposta.headers.setdefault("X-Content-Type-Options", "nosniff")
        resposta.headers.setdefault("X-Frame-Options", "DENY")
        resposta.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        resposta.headers.setdefault(
            "Permissions-Policy", "camera=(), microphone=(), geolocation=(), interest-cohort=()"
        )
        # Tudo vem do próprio site, inclusive as fontes (RNF10: nenhum serviço
        # de terceiros recebe dados do visitante).
        resposta.headers.setdefault(
            "Content-Security-Policy",
            "default-src 'self'; img-src 'self' data:; style-src 'self'; font-src 'self'; "
            "script-src 'self'; connect-src 'self'; manifest-src 'self'; worker-src 'self'; "
            "frame-ancestors 'none'; form-action 'self'; base-uri 'self'",
        )
        if app.config.get("SESSION_COOKIE_SECURE"):
            resposta.headers.setdefault(
                "Strict-Transport-Security", "max-age=31536000; includeSubDomains"
            )
        return resposta
