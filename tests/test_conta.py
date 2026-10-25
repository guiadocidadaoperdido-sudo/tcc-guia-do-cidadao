"""Testes da conta do cidadão: cadastro, entrar, sair, minha área e excluir conta."""
import pytest

from app import create_app
from app.extensions import db
from app.models import Acompanhamento, Conteudo, Usuario
from config import ConfigTeste

from conftest import EMAIL, EMAIL_ADMIN, SENHA, SENHA_ADMIN, _cadastrar, _popular


# ---------- Cadastro ----------

def test_cadastro_cria_conta_e_ja_entra(cliente):
    resposta = _cadastrar(cliente, email="  Maria@Exemplo.com.BR ")
    assert resposta.headers["Location"].endswith("/conta/")
    usuario = Usuario.query.one()
    assert usuario.email == EMAIL  # guardado sem espaços e em minúsculas
    assert usuario.consentimento_em is not None
    assert usuario.senha_hash != SENHA
    assert EMAIL in cliente.get("/conta/").get_data(as_text=True)


def test_cadastro_sem_consentimento_e_recusado(cliente):
    html = _cadastrar(cliente, consentimento=None).get_data(as_text=True)
    assert "marque que você concorda" in html
    assert Usuario.query.count() == 0


@pytest.mark.parametrize("senha, confirmar, mensagem", [
    ("curta", "curta", "pelo menos 8 caracteres"),
    ("senha-longa-1", "senha-longa-2", "não são iguais"),
])
def test_cadastro_confere_a_senha(cliente, senha, confirmar, mensagem):
    html = _cadastrar(cliente, senha=senha, confirmar=confirmar).get_data(as_text=True)
    assert mensagem in html
    assert Usuario.query.count() == 0


def test_cadastro_com_email_repetido(cliente):
    _cadastrar(cliente)
    cliente.post("/conta/sair")
    html = _cadastrar(cliente, email=EMAIL.upper()).get_data(as_text=True)
    assert "Já existe uma conta com esse e-mail" in html
    assert Usuario.query.count() == 1


# ---------- Entrar e sair ----------

def test_entrar_e_sair(cidadao_logado):
    cliente = cidadao_logado
    cliente.post("/conta/sair")
    assert cliente.get("/conta/").headers["Location"].endswith("/conta/entrar")

    resposta = cliente.post("/conta/entrar", data={"email": EMAIL, "senha": SENHA})
    assert resposta.headers["Location"].endswith("/conta/")
    assert cliente.get("/conta/").status_code == 200


def test_entrar_com_senha_errada(cidadao_logado):
    cliente = cidadao_logado
    cliente.post("/conta/sair")
    html = cliente.post("/conta/entrar", data={"email": EMAIL, "senha": "errada-123"}).get_data(as_text=True)
    assert "E-mail ou senha incorretos." in html
    assert cliente.get("/conta/").status_code == 302


def test_minha_area_exige_conta(cliente):
    resposta = cliente.get("/conta/")
    assert resposta.status_code == 302
    assert resposta.headers["Location"].endswith("/conta/entrar")


def test_sessao_acaba_ao_fechar_o_navegador(cidadao_logado):
    with cidadao_logado.session_transaction() as sessao:
        assert sessao.permanent is False
        assert "cidadao_id" in sessao


def test_cidadao_nao_entra_na_area_administrativa(cidadao_logado):
    resposta = cidadao_logado.get("/admin/")
    assert resposta.status_code == 302
    assert "/admin/login" in resposta.headers["Location"]


def test_sair_da_conta_nao_desloga_o_admin(admin_logado):
    cliente = admin_logado
    _cadastrar(cliente)
    cliente.post("/conta/sair")
    assert cliente.get("/admin/").status_code == 200


def test_menu_mostra_entrar_ou_minha_area(cliente):
    assert "Entrar ou criar conta" in cliente.get("/").get_data(as_text=True)
    _cadastrar(cliente)
    assert "Minha área" in cliente.get("/").get_data(as_text=True)


def test_paginas_da_conta_nao_ficam_em_cache(cidadao_logado):
    assert cidadao_logado.get("/conta/").headers["Cache-Control"] == "no-store"


# ---------- Excluir conta (LGPD) ----------

def test_excluir_conta_pede_a_senha(cidadao_logado):
    resposta = cidadao_logado.post("/conta/excluir", data={"senha": "errada-123"})
    assert resposta.headers["Location"].endswith("/conta/#excluir")
    assert Usuario.query.count() == 1


def test_excluir_conta_apaga_os_dados_pessoais_e_sai(cidadao_logado):
    usuario = Usuario.query.one()
    cnh = Conteudo.query.filter_by(slug="primeira-habilitacao-cnh").one()
    db.session.add(Acompanhamento(usuario=usuario, conteudo=cnh))
    db.session.commit()

    resposta = cidadao_logado.post("/conta/excluir", data={"senha": SENHA})
    assert resposta.headers["Location"].endswith("/")
    db.session.expire_all()
    # A linha fica, mas sem e-mail e sem senha (aparece em "Contas excluídas").
    usuario = Usuario.query.one()
    assert usuario.email is None and usuario.senha_hash is None
    assert usuario.status == "excluido" and usuario.excluida_em is not None
    assert Acompanhamento.query.count() == 0
    assert cidadao_logado.get("/conta/").status_code == 302
    # Não dá mais para entrar com o e-mail antigo...
    html = cidadao_logado.post("/conta/entrar", data={"email": EMAIL, "senha": SENHA}).get_data(as_text=True)
    assert "E-mail ou senha incorretos." in html
    # ...mas a pessoa pode criar uma conta nova com o mesmo e-mail.
    _cadastrar(cidadao_logado)
    assert Usuario.query.filter_by(email=EMAIL, status="ativo").count() == 1


def test_minha_area_mostra_tema_salvo(cidadao_logado):
    usuario = Usuario.query.one()
    cnh = Conteudo.query.filter_by(slug="primeira-habilitacao-cnh").one()
    db.session.add(Acompanhamento(usuario=usuario, conteudo=cnh))
    db.session.commit()
    assert "Primeira habilitação (CNH)" in cidadao_logado.get("/conta/").get_data(as_text=True)


# ---------- Limite de tentativas ----------

class ConfigComLimite(ConfigTeste):
    RATELIMIT_ENABLED = True
    LIMITE_LOGIN = "3 per minute"


def test_entrar_tem_limite_de_tentativas():
    app = create_app(ConfigComLimite)
    with app.app_context():
        db.create_all()
        _popular()
        cliente = app.test_client()
        codigos = [
            cliente.post("/conta/entrar", data={"email": EMAIL, "senha": "x"}).status_code
            for _ in range(4)
        ]
        assert codigos[:3] == [200, 200, 200]
        assert codigos[3] == 429
        db.session.remove()
        db.drop_all()
