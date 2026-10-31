from app.cli import criar_admin_pelo_ambiente
from app.models import Administrador


def test_cria_admin_pelas_variaveis(app, monkeypatch):
    monkeypatch.setenv("ADMIN_EMAIL", "Projeto@Exemplo.com.br ")
    monkeypatch.setenv("ADMIN_SENHA", "senha-forte-123")
    monkeypatch.setenv("ADMIN_NOME", "Equipe do TCC")
    criar_admin_pelo_ambiente()
    admin = Administrador.query.filter_by(email="projeto@exemplo.com.br").first()
    assert admin is not None
    assert admin.nome == "Equipe do TCC"
    assert admin.conferir_senha("senha-forte-123")


def test_nao_duplica_admin_existente(app, monkeypatch):
    monkeypatch.setenv("ADMIN_EMAIL", "projeto@exemplo.com.br")
    monkeypatch.setenv("ADMIN_SENHA", "senha-forte-123")
    criar_admin_pelo_ambiente()
    criar_admin_pelo_ambiente()
    assert Administrador.query.filter_by(email="projeto@exemplo.com.br").count() == 1


def test_sem_variaveis_ou_senha_curta_nao_cria(app, monkeypatch):
    total = Administrador.query.count()
    monkeypatch.delenv("ADMIN_EMAIL", raising=False)
    monkeypatch.delenv("ADMIN_SENHA", raising=False)
    criar_admin_pelo_ambiente()
    monkeypatch.setenv("ADMIN_EMAIL", "outro@exemplo.com.br")
    monkeypatch.setenv("ADMIN_SENHA", "curta")
    criar_admin_pelo_ambiente()
    assert Administrador.query.count() == total
