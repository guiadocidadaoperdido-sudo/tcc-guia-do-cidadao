"""Testes do verificador de golpe, da denúncia de link e da revisão no admin."""
import pytest

from app.extensions import db
from app.models import LinkDenunciado
from app.models.link_denunciado import CONFIRMADO, DESCARTADO, PENDENTE
from app.verificador import ALTO, ATENCAO, SEM_SINAIS, achar_links, dominio_de, verificar

from conftest import _cadastrar

GOLPE = "golpe-detran.com"


# ---------- Regras do verificador (sem banco) ----------

@pytest.mark.parametrize("texto, nivel", [
    # Endereço que imita o governo
    ("Seu CPF será bloqueado. Regularize em https://gov-br.regulariza.com/cpf", ALTO),
    ("Consulte sua restituição: receitafederal-consulta.com", ALTO),
    # Pede código: golpe sempre, mesmo com link oficial
    ("Para liberar seu benefício, informe o código que chegou por SMS", ALTO),
    # Pix + link que não é oficial
    ("Pague a taxa via Pix em loja-pagamentos.com", ALTO),
    # Número no lugar do nome do site
    ("Acesse http://192.168.10.5/login", ALTO),
    # Sinais de atenção, sem nada decisivo
    ("Seu benefício foi liberado, acesse bit.ly/abc", ATENCAO),
    ("Promoção em www.pisos.com.br", ATENCAO),
    ("Urgente: pagamento do boleto vence hoje", ATENCAO),
    # Sites oficiais e mensagens sem sinais
    ("Calendário do Bolsa Família: https://www.gov.br/mds/pt-br", SEM_SINAIS),
    ("Faça o alistamento em alistamento.eb.mil.br", SEM_SINAIS),
    ("Oi, tudo bem? Amanhã tem reunião na escola.", SEM_SINAIS),
])
def test_niveis_do_verificador(texto, nivel):
    assert verificar(texto).nivel == nivel


def test_resultado_sem_sinais_nao_tem_motivos():
    resultado = verificar("https://www.gov.br/inss")
    assert resultado.motivos == []
    assert resultado.links[0].oficial


def test_dominio_denunciado_vira_muito_suspeito():
    resultado = verificar(f"Veja www.{GOLPE}/multa", denunciados={GOLPE})
    assert resultado.nivel == ALTO
    assert "denunciado e confirmado" in resultado.motivos[0]


def test_dominio_que_so_termina_parecido_nao_e_oficial():
    # "gov.br.site.com" e "fakegov.br" não terminam em .gov.br de verdade.
    assert not achar_links("https://gov.br.site.com/x")[0].oficial
    assert not achar_links("https://fakegov.br")[0].oficial
    assert achar_links("https://servicos.receita.fazenda.gov.br")[0].oficial


def test_acha_links_no_meio_da_mensagem():
    links = achar_links("Clique: https://a-b.com/x?y=1, ou www.teste.net. Obrigado!")
    assert [l.url for l in links] == ["https://a-b.com/x?y=1", "www.teste.net"]
    assert dominio_de("HTTPS://WWW.Gov.BR/inss") == "www.gov.br"


# ---------- Página /verificar-golpe ----------

def test_pagina_do_verificador_abre_para_todos(cliente):
    html = cliente.get("/verificar-golpe").get_data(as_text=True)
    assert "Verificar golpe" in html
    assert "crie uma conta" in html  # sem conta: convite para denunciar


def test_verificar_mostra_resultado_e_nao_guarda_nada(cliente):
    resposta = cliente.post("/verificar-golpe", data={"texto": "Pague a taxa por Pix em golpe-gov.com"})
    html = resposta.get_data(as_text=True)
    assert "Muito suspeito" in html
    assert "<code>golpe-gov.com</code>" in html
    assert resposta.headers["Cache-Control"] == "no-store"
    assert LinkDenunciado.query.count() == 0


def test_verificar_sem_texto(cliente):
    html = cliente.post("/verificar-golpe", data={"texto": ""}).get_data(as_text=True)
    assert "Cole um link ou uma mensagem" in html


def test_verificador_usa_os_golpes_confirmados(cliente):
    db.session.add(LinkDenunciado(url=f"https://{GOLPE}/pagar", dominio=GOLPE, status=CONFIRMADO))
    db.session.add(LinkDenunciado(url="https://ainda-pendente.com", dominio="ainda-pendente.com"))
    db.session.commit()
    html = cliente.post("/verificar-golpe", data={"texto": f"{GOLPE}/outra"}).get_data(as_text=True)
    assert "já foi denunciado e confirmado" in html
    html = cliente.post("/verificar-golpe", data={"texto": "ainda-pendente.com"}).get_data(as_text=True)
    assert "já foi denunciado" not in html


# ---------- Denúncia (só com conta) ----------

def test_denuncia_exige_conta(cliente):
    resposta = cliente.post("/conta/denuncias", data={"url": GOLPE})
    assert resposta.headers["Location"].endswith("/conta/entrar")
    assert LinkDenunciado.query.count() == 0


def test_denunciar_link(cidadao_logado):
    html = cidadao_logado.post("/verificar-golpe", data={"texto": f"Pague em {GOLPE}"}).get_data(as_text=True)
    assert "Denunciar este link" in html

    cidadao_logado.post("/conta/denuncias", data={"url": GOLPE, "descricao": "SMS de multa"})
    cidadao_logado.post("/conta/denuncias", data={"url": GOLPE})  # repetida não duplica
    denuncia = LinkDenunciado.query.one()
    assert denuncia.url == f"https://{GOLPE}"
    assert denuncia.dominio == GOLPE
    assert denuncia.status == PENDENTE
    assert denuncia.descricao == "SMS de multa"


@pytest.mark.parametrize("url, mensagem", [
    ("https://www.gov.br/inss", "é um endereço oficial"),
    ("javascript:alert(1)", "não parece um link"),
    ("nada aqui", "não parece um link"),
])
def test_denuncia_recusada(cidadao_logado, url, mensagem):
    resposta = cidadao_logado.post("/conta/denuncias", data={"url": url}, follow_redirects=True)
    assert mensagem in resposta.get_data(as_text=True)
    assert LinkDenunciado.query.count() == 0


def test_mesmo_link_de_outra_pessoa_nao_duplica(cliente):
    _cadastrar(cliente)
    cliente.post("/conta/denuncias", data={"url": GOLPE})
    cliente.post("/conta/sair")
    _cadastrar(cliente, email="joao@exemplo.com.br")
    cliente.post("/conta/denuncias", data={"url": GOLPE})
    assert LinkDenunciado.query.count() == 1


def test_dominio_ja_confirmado_nao_vira_nova_denuncia(cidadao_logado):
    db.session.add(LinkDenunciado(url=f"https://{GOLPE}", dominio=GOLPE, status=CONFIRMADO))
    db.session.commit()
    html = cidadao_logado.post("/conta/denuncias", data={"url": f"{GOLPE}/outra"},
                               follow_redirects=True).get_data(as_text=True)
    assert "já está confirmado como golpe" in html
    assert LinkDenunciado.query.count() == 1


def test_excluir_conta_mantem_denuncia_sem_dono(cidadao_logado):
    from conftest import SENHA
    cidadao_logado.post("/conta/denuncias", data={"url": GOLPE})
    cidadao_logado.post("/conta/excluir", data={"senha": SENHA})
    denuncia = LinkDenunciado.query.one()
    assert denuncia.usuario is None


# ---------- Revisão no admin ----------

def test_admin_confirma_descarta_e_reabre(admin_logado):
    db.session.add(LinkDenunciado(url=f"https://{GOLPE}", dominio=GOLPE))
    db.session.commit()
    denuncia = LinkDenunciado.query.one()

    html = admin_logado.get("/admin/denuncias").get_data(as_text=True)
    assert GOLPE in html
    assert f'href="https://{GOLPE}' not in html  # o link nunca é clicável

    resposta = admin_logado.post(f"/admin/denuncias/{denuncia.id}/confirmar")
    assert resposta.headers["Location"].endswith("/admin/denuncias")
    assert denuncia.status == CONFIRMADO
    assert denuncia.administrador is not None and denuncia.revisado_em is not None
    assert GOLPE in admin_logado.get("/admin/denuncias/confirmadas").get_data(as_text=True)

    admin_logado.post(f"/admin/denuncias/{denuncia.id}/reabrir")
    assert denuncia.status == PENDENTE and denuncia.revisado_em is None
    admin_logado.post(f"/admin/denuncias/{denuncia.id}/descartar")
    assert denuncia.status == DESCARTADO


def test_admin_acao_invalida(admin_logado):
    db.session.add(LinkDenunciado(url=f"https://{GOLPE}", dominio=GOLPE))
    db.session.commit()
    assert admin_logado.post("/admin/denuncias/1/apagar").status_code == 404


def test_cidadao_nao_ve_denuncias_do_admin(cidadao_logado):
    assert cidadao_logado.get("/admin/denuncias").status_code == 302
