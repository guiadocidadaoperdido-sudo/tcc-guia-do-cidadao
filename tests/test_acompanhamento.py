"""Testes do "Meu acompanhamento": salvar tema, marcar documentos e passos e aviso de novidade."""
from datetime import datetime, timedelta

from app.extensions import db
from app.models import Acompanhamento, Conteudo

from conftest import _cadastrar

URL_CNH = "/conteudo/primeira-habilitacao-cnh"
TEMA = "/conta/temas/primeira-habilitacao-cnh"
FETCH = {"X-Requested-With": "fetch"}


def _acompanhamento():
    return Acompanhamento.query.one_or_none()


# ---------- Sem conta ----------

def test_sem_conta_aparece_convite_e_checklist_no_aparelho(cliente):
    html = cliente.get(URL_CNH).get_data(as_text=True)
    assert "crie uma conta" in html
    assert "fica só neste aparelho" in html
    assert 'id="form-progresso"' not in html
    assert "Salvar este tema" not in html


def test_sem_conta_nao_salva_nada(cliente):
    resposta = cliente.post(f"{TEMA}/salvar")
    assert resposta.headers["Location"].endswith("/conta/entrar")
    resposta = cliente.post(f"{TEMA}/progresso", data={"passos": "1"}, headers=FETCH)
    assert resposta.status_code == 401
    assert _acompanhamento() is None


# ---------- Salvar e remover ----------

def test_salvar_e_remover_tema(cidadao_logado):
    assert "Salvar este tema" in cidadao_logado.get(URL_CNH).get_data(as_text=True)

    cidadao_logado.post(f"{TEMA}/salvar")
    cidadao_logado.post(f"{TEMA}/salvar")  # clicar duas vezes não duplica
    assert Acompanhamento.query.count() == 1
    html = cidadao_logado.get(URL_CNH).get_data(as_text=True)
    assert "Tema salvo na sua conta" in html
    assert "Remover dos meus temas" in html

    cidadao_logado.post(f"{TEMA}/remover")
    assert _acompanhamento() is None


def test_nao_salva_conteudo_em_rascunho(cidadao_logado):
    resposta = cidadao_logado.post("/conta/temas/minha-casa-minha-vida/salvar")
    assert resposta.status_code == 404
    assert _acompanhamento() is None


# ---------- Documentos e passos ----------

def test_marcar_ja_salva_o_tema_e_guarda_o_andamento(cidadao_logado):
    resposta = cidadao_logado.post(
        f"{TEMA}/progresso", data={"documentos": ["2"], "passos": ["1"]}, headers=FETCH
    )
    assert resposta.get_json() == {
        "ok": True, "mensagem": "Andamento salvo na sua conta.", "passo_atual": 1,
    }
    item = _acompanhamento()
    assert item.documentos_marcados == [2]
    assert item.passo_atual == 1

    # As marcações voltam marcadas ao abrir a página de novo.
    html = cidadao_logado.get(URL_CNH).get_data(as_text=True)
    assert 'name="documentos" value="2" form="form-progresso" checked' in html
    assert 'name="passos" value="1" form="form-progresso" checked' in html
    assert 'name="passos" value="2" form="form-progresso">' in html


def test_marcar_um_passo_conta_os_anteriores(cidadao_logado):
    # Sem JavaScript, só a caixinha do passo 2 chega: os passos 1 e 2 contam como feitos.
    cidadao_logado.post(f"{TEMA}/progresso", data={"passos": ["2"]})
    assert _acompanhamento().passo_atual == 2


def test_progresso_ignora_numeros_invalidos(cidadao_logado):
    # A CNH de teste tem 2 documentos e 2 passos. "²" passa no isdigit(), mas não é número.
    cidadao_logado.post(
        f"{TEMA}/progresso",
        data={"documentos": ["1", "1", "9", "0", "abc", "²"], "passos": ["7", "-1", "²"]},
        headers=FETCH,
    )
    item = _acompanhamento()
    assert item.documentos_marcados == [1]
    assert item.passo_atual == 0


def test_desmarcar_tudo(cidadao_logado):
    cidadao_logado.post(f"{TEMA}/progresso", data={"documentos": ["1", "2"], "passos": ["2"]})
    cidadao_logado.post(f"{TEMA}/progresso", data={}, headers=FETCH)
    item = _acompanhamento()
    assert item.documentos_marcados == []
    assert item.passo_atual == 0


def test_minha_area_mostra_o_andamento(cidadao_logado):
    cidadao_logado.post(f"{TEMA}/progresso", data={"documentos": ["1"], "passos": ["2"]})
    html = cidadao_logado.get("/conta/").get_data(as_text=True)
    assert "Passos: 2 de 2" in html
    assert "Documentos: 1 de 2" in html

    resposta = cidadao_logado.post(f"{TEMA}/remover", data={"origem": "minha_area"})
    assert "/conta/" in resposta.headers["Location"]
    assert _acompanhamento() is None


def test_tema_de_outra_pessoa_nao_aparece(cliente):
    _cadastrar(cliente)
    cliente.post(f"{TEMA}/progresso", data={"passos": ["2"]})
    cliente.post("/conta/sair")

    _cadastrar(cliente, email="joao@exemplo.com.br")
    html = cliente.get(URL_CNH).get_data(as_text=True)
    assert "Salvar este tema" in html
    assert 'value="2" form="form-progresso" checked' not in html


# ---------- Aviso de novidade ----------

def test_aviso_quando_o_conteudo_mudou_depois_da_visita(cidadao_logado):
    cidadao_logado.post(f"{TEMA}/salvar")
    item = _acompanhamento()
    item.visto_em = datetime.now() - timedelta(days=10)
    Conteudo.query.filter_by(slug="primeira-habilitacao-cnh").one().atualizado_em = (
        datetime.now() - timedelta(days=2)
    )
    db.session.commit()

    html = cidadao_logado.get(URL_CNH).get_data(as_text=True)
    assert "depois da sua última visita" in html

    # Abriu a página: o aviso some na próxima visita.
    html = cidadao_logado.get(URL_CNH).get_data(as_text=True)
    assert "depois da sua última visita" not in html


def test_pagina_com_andamento_nao_fica_em_cache(cidadao_logado, cliente):
    assert cidadao_logado.get(URL_CNH).headers["Cache-Control"] == "no-store"
    cidadao_logado.post("/conta/sair")
    assert "no-store" not in cliente.get(URL_CNH).headers.get("Cache-Control", "")
