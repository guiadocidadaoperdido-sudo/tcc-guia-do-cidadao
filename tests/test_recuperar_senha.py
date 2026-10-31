"""Testes do "esqueci minha senha": pedir o link, usar o link e os casos de link inválido."""
import re
import urllib.request
from unittest import mock

import pytest

from app.extensions import db
from app.models import Usuario

from conftest import EMAIL, SENHA, _cadastrar

NOVA_SENHA = "senha-nova-da-maria"


@pytest.fixture
def emails_enviados(monkeypatch):
    """Guarda os e-mails em vez de mandar (troca o enviar_email do controller)."""
    enviados = []

    def falso(para, assunto, texto):
        enviados.append({"para": para, "assunto": assunto, "texto": texto})
        return True

    monkeypatch.setattr("app.controllers.conta.enviar_email", falso)
    return enviados


@pytest.fixture
def conta_criada(cliente):
    _cadastrar(cliente)
    cliente.post("/conta/sair")
    return cliente


def _pedir_link(cliente, email=EMAIL):
    return cliente.post("/conta/esqueci-senha", data={"email": email})


def _link_do_email(email):
    return re.search(r"http://localhost(/conta/redefinir-senha/\S+)", email["texto"]).group(1)


def _redefinir(cliente, caminho, senha=NOVA_SENHA, confirmar=None):
    return cliente.post(caminho, data={"senha": senha, "confirmar_senha": confirmar or senha})


# ---------- Pedir o link ----------

def test_tela_de_entrar_tem_link_para_esqueci_a_senha(cliente):
    assert "/conta/esqueci-senha" in cliente.get("/conta/entrar").get_data(as_text=True)


def test_pedir_link_manda_email_com_o_link(conta_criada, emails_enviados):
    resposta = _pedir_link(conta_criada, email="  MARIA@exemplo.com.br ")
    assert resposta.headers["Location"].endswith("/conta/entrar")
    assert len(emails_enviados) == 1
    assert emails_enviados[0]["para"] == EMAIL
    assert "1 hora" in emails_enviados[0]["texto"]
    assert _link_do_email(emails_enviados[0])


def test_email_sem_conta_tem_a_mesma_resposta_e_nao_manda_nada(conta_criada, emails_enviados):
    com_conta = _pedir_link(conta_criada).headers["Location"]
    aviso_com_conta = conta_criada.get(com_conta).get_data(as_text=True)
    sem_conta = _pedir_link(conta_criada, email="ninguem@exemplo.com.br").headers["Location"]
    aviso_sem_conta = conta_criada.get(sem_conta).get_data(as_text=True)

    assert com_conta == sem_conta
    assert "Se existir uma conta com esse e-mail" in aviso_com_conta
    assert "Se existir uma conta com esse e-mail" in aviso_sem_conta
    assert len(emails_enviados) == 1


def test_conta_bloqueada_nao_recebe_link(conta_criada, emails_enviados):
    usuario = Usuario.query.one()
    usuario.bloquear("Motivo de teste do bloqueio", None)
    db.session.commit()
    _pedir_link(conta_criada)
    assert emails_enviados == []


# ---------- Usar o link ----------

def test_link_cria_senha_nova_e_ja_entra(conta_criada, emails_enviados):
    _pedir_link(conta_criada)
    caminho = _link_do_email(emails_enviados[0])
    assert conta_criada.get(caminho).status_code == 200

    resposta = _redefinir(conta_criada, caminho)
    assert resposta.headers["Location"].endswith("/conta/")
    assert conta_criada.get("/conta/").status_code == 200

    conta_criada.post("/conta/sair")
    antiga = conta_criada.post("/conta/entrar", data={"email": EMAIL, "senha": SENHA})
    assert "E-mail ou senha incorretos" in antiga.get_data(as_text=True)
    nova = conta_criada.post("/conta/entrar", data={"email": EMAIL, "senha": NOVA_SENHA})
    assert nova.headers["Location"].endswith("/conta/")


def test_link_so_funciona_uma_vez(conta_criada, emails_enviados):
    _pedir_link(conta_criada)
    caminho = _link_do_email(emails_enviados[0])
    _redefinir(conta_criada, caminho)
    conta_criada.post("/conta/sair")

    resposta = conta_criada.get(caminho)
    assert resposta.headers["Location"].endswith("/conta/esqueci-senha")
    _redefinir(conta_criada, caminho, senha="outra-senha-qualquer")
    assert Usuario.query.one().conferir_senha(NOVA_SENHA)


def test_senhas_diferentes_nao_trocam_a_senha(conta_criada, emails_enviados):
    _pedir_link(conta_criada)
    caminho = _link_do_email(emails_enviados[0])
    html = _redefinir(conta_criada, caminho, confirmar="outra-coisa-123").get_data(as_text=True)
    assert "não são iguais" in html
    assert Usuario.query.one().conferir_senha(SENHA)


def test_link_inventado_nao_funciona(cliente):
    resposta = cliente.get("/conta/redefinir-senha/qualquer-coisa")
    assert resposta.headers["Location"].endswith("/conta/esqueci-senha")


def test_link_vencido_nao_funciona(app, conta_criada, emails_enviados):
    _pedir_link(conta_criada)
    caminho = _link_do_email(emails_enviados[0])
    app.config["VALIDADE_LINK_SENHA"] = -1  # finge que já passou da validade
    assert conta_criada.get(caminho).headers["Location"].endswith("/conta/esqueci-senha")


def test_link_de_conta_excluida_nao_funciona(conta_criada, emails_enviados):
    _pedir_link(conta_criada)
    caminho = _link_do_email(emails_enviados[0])
    Usuario.query.one().excluir_conta()
    db.session.commit()
    assert conta_criada.get(caminho).headers["Location"].endswith("/conta/esqueci-senha")


# ---------- Envio do e-mail (app/envio_email.py) ----------

def test_sem_email_configurado_so_escreve_no_log(app):
    from app.envio_email import enviar_email
    with mock.patch.object(app.logger, "warning") as aviso, \
            mock.patch.object(urllib.request, "urlopen") as urlopen:
        assert enviar_email(EMAIL, "Assunto", "link-de-teste") is True
    assert "link-de-teste" in aviso.call_args.args
    urlopen.assert_not_called()


def test_envio_pelo_brevo_monta_o_pedido_certo(app):
    from app.envio_email import enviar_email
    app.config["BREVO_API_KEY"] = "chave-de-teste"
    with mock.patch.object(urllib.request, "urlopen") as urlopen:
        assert enviar_email(EMAIL, "Assunto", "Texto") is True
    pedido = urlopen.call_args.args[0]
    assert pedido.full_url == "https://api.brevo.com/v3/smtp/email"
    assert pedido.get_header("Api-key") == "chave-de-teste"
    assert b'"email": "guiadocidadaoperdido@gmail.com"' in pedido.data


def test_falha_no_envio_nao_quebra_a_pagina(app):
    from app.envio_email import enviar_email
    app.config["BREVO_API_KEY"] = "chave-de-teste"
    with mock.patch.object(urllib.request, "urlopen", side_effect=OSError("sem internet")):
        assert enviar_email(EMAIL, "Assunto", "Texto") is False
