"""Testes das telas de contas no admin: ativas, bloqueadas e excluídas (padrão do FacilMed)."""
from datetime import datetime

import pytest
from sqlalchemy.exc import IntegrityError

from app.extensions import db
from app.models import Usuario


def _conta(email, status="ativo"):
    usuario = Usuario(email=email, consentimento_em=datetime.now())
    usuario.definir_senha("senha-do-cidadao")
    db.session.add(usuario)
    db.session.commit()
    if status == "bloqueado":
        usuario.bloquear("Usou a conta para mandar links falsos.", None)
    elif status == "excluido":
        usuario.excluir_conta()
    db.session.commit()
    return usuario


@pytest.fixture
def tres_contas(app):
    return _conta("ativa@exemplo.com.br"), _conta("bloq@exemplo.com.br", "bloqueado"), \
        _conta("saiu@exemplo.com.br", "excluido")


def test_so_admin_abre_as_telas_de_contas(cliente):
    for caminho in ("/admin/usuarios", "/admin/usuarios/bloqueadas", "/admin/usuarios/excluidas"):
        assert cliente.get(caminho).status_code == 302


def test_cada_tela_mostra_so_as_contas_daquela_situacao(admin_logado, tres_contas):
    ativas = admin_logado.get("/admin/usuarios").get_data(as_text=True)
    bloqueadas = admin_logado.get("/admin/usuarios/bloqueadas").get_data(as_text=True)
    excluidas = admin_logado.get("/admin/usuarios/excluidas").get_data(as_text=True)

    assert "ativa@exemplo.com.br" in ativas and "bloq@exemplo.com.br" not in ativas
    assert "bloq@exemplo.com.br" in bloqueadas and "ativa@exemplo.com.br" not in bloqueadas
    assert "Usou a conta para mandar links falsos." in bloqueadas  # motivo interno
    # A conta excluída não mostra mais o e-mail, só o número.
    assert "saiu@exemplo.com.br" not in excluidas
    assert f"Conta nº {tres_contas[2].id}" in excluidas


def test_abas_mostram_o_total_de_cada_situacao(admin_logado, tres_contas):
    html = admin_logado.get("/admin/usuarios").get_data(as_text=True)
    assert html.count('class="aba__total">1<') == 3


def test_acoes_certas_em_cada_tela(admin_logado, tres_contas):
    assert "Confirmar bloqueio" in admin_logado.get("/admin/usuarios").get_data(as_text=True)
    assert "Desbloquear" in admin_logado.get("/admin/usuarios/bloqueadas").get_data(as_text=True)
    excluidas = admin_logado.get("/admin/usuarios/excluidas").get_data(as_text=True)
    assert "Confirmar bloqueio" not in excluidas and "Desbloquear</button>" not in excluidas


def test_bloquear_exige_motivo(admin_logado, tres_contas):
    ativa = tres_contas[0]
    admin_logado.post(f"/admin/usuarios/{ativa.id}/bloquear", data={"motivo": "curto"})
    db.session.expire_all()
    assert db.session.get(Usuario, ativa.id).status == "ativo"


def test_bloquear_e_desbloquear(admin_logado, tres_contas):
    ativa = tres_contas[0]
    resposta = admin_logado.post(f"/admin/usuarios/{ativa.id}/bloquear",
                                 data={"motivo": "Conta usada para spam de links."})
    assert resposta.headers["Location"].endswith("/admin/usuarios")
    db.session.expire_all()
    conta = db.session.get(Usuario, ativa.id)
    assert conta.status == "bloqueado"
    assert conta.bloqueado_por.email == "admin@exemplo.com.br"
    assert conta.bloqueado_em is not None

    admin_logado.post(f"/admin/usuarios/{ativa.id}/desbloquear")
    db.session.expire_all()
    conta = db.session.get(Usuario, ativa.id)
    assert conta.status == "ativo" and conta.motivo_bloqueio is None


def test_conta_excluida_nao_pode_ser_bloqueada_nem_desbloqueada(admin_logado, tres_contas):
    excluida = tres_contas[2]
    admin_logado.post(f"/admin/usuarios/{excluida.id}/bloquear",
                      data={"motivo": "Tentando reativar pela porta dos fundos."})
    admin_logado.post(f"/admin/usuarios/{excluida.id}/desbloquear")
    db.session.expire_all()
    assert db.session.get(Usuario, excluida.id).status == "excluido"


def test_banco_nao_deixa_reativar_conta_excluida(app, tres_contas):
    excluida = tres_contas[2]
    excluida.status = "ativo"
    with pytest.raises(IntegrityError):
        db.session.commit()
    db.session.rollback()


def test_bloqueado_nao_entra_e_quem_estava_logado_sai(cliente, app):
    cliente.post("/conta/cadastrar", data={
        "email": "joao@exemplo.com.br", "senha": "senha-do-joao",
        "confirmar_senha": "senha-do-joao", "consentimento": "y",
    })
    assert cliente.get("/conta/").status_code == 200

    conta = Usuario.query.filter_by(email="joao@exemplo.com.br").one()
    conta.bloquear("Conta usada para spam de links.", None)
    db.session.commit()

    # Quem já estava logado cai fora na próxima página.
    assert cliente.get("/conta/").status_code == 302
    html = cliente.post("/conta/entrar", data={
        "email": "joao@exemplo.com.br", "senha": "senha-do-joao",
    }).get_data(as_text=True)
    assert "Sua conta está bloqueada" in html
    assert "spam" not in html  # o motivo é interno


def test_busca_por_email(admin_logado, tres_contas):
    _conta("outra@exemplo.com.br")
    html = admin_logado.get("/admin/usuarios?busca=outra").get_data(as_text=True)
    assert "outra@exemplo.com.br" in html and "ativa@exemplo.com.br" not in html


def test_admin_exclui_dados_de_conta_bloqueada_a_pedido(admin_logado, tres_contas):
    bloqueada, ativa = tres_contas[1], tres_contas[0]
    admin_logado.post(f"/admin/usuarios/{bloqueada.id}/excluir-dados")
    admin_logado.post(f"/admin/usuarios/{ativa.id}/excluir-dados")  # ativa: recusado
    db.session.expire_all()
    conta = db.session.get(Usuario, bloqueada.id)
    assert conta.status == "excluido" and conta.email is None
    assert db.session.get(Usuario, ativa.id).status == "ativo"
