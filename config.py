"""Configurações do Flask.

Os valores sensíveis (chave secreta e endereço do banco) vêm do arquivo .env,
que não vai para o repositório. Veja o modelo em .env.example.
"""
import os

from dotenv import load_dotenv

PASTA_BASE = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(PASTA_BASE, ".env"))


def _endereco_do_banco(variavel="DATABASE_URL", padrao=None):
    url = os.environ.get(variavel)
    if not url and padrao:
        return padrao
    if not url:
        # Sem .env, usa um arquivo SQLite local só para desenvolvimento.
        return "sqlite:///" + os.path.join(PASTA_BASE, "instance", "guia.db")
    # O SQLAlchemy precisa saber que o driver é o psycopg (versão 3).
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql+psycopg://", 1)
    elif url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+psycopg://", 1)
    return url


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "troque-esta-chave-no-arquivo-env")
    SQLALCHEMY_DATABASE_URI = _endereco_do_banco()
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    # Se o PostgreSQL estiver desligado, desiste em 5 segundos em vez de
    # deixar a página carregando sem fim. O pre_ping refaz a conexão quando o
    # banco na nuvem a encerra por inatividade.
    if SQLALCHEMY_DATABASE_URI.startswith("postgresql"):
        SQLALCHEMY_ENGINE_OPTIONS = {
            "connect_args": {"connect_timeout": 5},
            "pool_pre_ping": True,
            "pool_recycle": 300,
        }

    # Cookies de sessão protegidos (RNF06 e RNF07)
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = os.environ.get("COOKIE_SEGURO", "0") == "1"
    REMEMBER_COOKIE_SECURE = SESSION_COOKIE_SECURE

    # Na nuvem (Render) o site fica atrás de um proxy que recebe o HTTPS.
    ATRAS_DE_PROXY = os.environ.get("ATRAS_DE_PROXY", "0") == "1"

    ITENS_POR_PAGINA = 10

    # Limite de tentativas (Flask-Limiter). Guardado na memória do servidor.
    RATELIMIT_STORAGE_URI = "memory://"
    RATELIMIT_HEADERS_ENABLED = True
    LIMITE_LOGIN = "5 per minute;20 per hour"
    LIMITE_AVALIACAO = "30 per hour"
    LIMITE_VERIFICADOR = "30 per hour"
    LIMITE_DENUNCIA = "10 per hour"
    LIMITE_ESQUECI_SENHA = "3 per minute;10 per hour"

    # E-mail do projeto (recuperação de senha). Veja app/envio_email.py.
    # No Render: BREVO_API_KEY. No PC: MAIL_SENHA (senha de app do Gmail).
    # Sem nenhum dos dois, o link aparece só no terminal.
    MAIL_REMETENTE = os.environ.get("MAIL_REMETENTE", "guiadocidadaoperdido@gmail.com")
    MAIL_REMETENTE_NOME = "Guia do Cidadão Perdido"
    BREVO_API_KEY = os.environ.get("BREVO_API_KEY")
    MAIL_SERVIDOR = os.environ.get("MAIL_SERVIDOR", "smtp.gmail.com")
    MAIL_PORTA = int(os.environ.get("MAIL_PORTA", "587"))
    MAIL_USUARIO = os.environ.get("MAIL_USUARIO")
    MAIL_SENHA = os.environ.get("MAIL_SENHA")
    # Por quanto tempo o link de "esqueci minha senha" funciona (em segundos).
    VALIDADE_LINK_SENHA = 3600

    # Nível dos registros (logs) mostrados no terminal e no painel do Render.
    NIVEL_LOG = os.environ.get("NIVEL_LOG", "INFO")


class ConfigTeste(Config):
    TESTING = True
    SECRET_KEY = "chave-de-teste"
    # Por padrão os testes usam SQLite em memória. Para testar no PostgreSQL,
    # defina TEST_DATABASE_URL com um banco vazio, só para testes.
    SQLALCHEMY_DATABASE_URI = _endereco_do_banco("TEST_DATABASE_URL", "sqlite:///:memory:")
    SQLALCHEMY_ENGINE_OPTIONS = (
        {"connect_args": {"connect_timeout": 5}}
        if SQLALCHEMY_DATABASE_URI.startswith("postgresql") else {}
    )
    WTF_CSRF_ENABLED = False
    # Nos testes o limite fica desligado; o teste do limite liga de novo.
    RATELIMIT_ENABLED = False
    NIVEL_LOG = "WARNING"
    # Os testes nunca mandam e-mail de verdade, mesmo com o .env preenchido.
    BREVO_API_KEY = None
    MAIL_SENHA = None
