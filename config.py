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
