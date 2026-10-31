"""Testes do glossário "O que é isso?": termos sublinhados, página pública e cadastro no admin."""
import pytest
from flask import g

from app.extensions import db
from app.glossario import marcar_termos
from app.models import Conteudo, TermoGlossario


@pytest.fixture
def termos(app):
    db.session.add_all([
        TermoGlossario(termo="CPF", explicacao="Cadastro de Pessoas Físicas."),
        TermoGlossario(termo="Cadastro Único", explicacao="Cadastro do governo para baixa renda."),
        TermoGlossario(termo="Cadastro", explicacao="Termo curto, para testar o maior primeiro."),
        TermoGlossario(termo="conta gov.br", explicacao="Login único do governo."),
    ])
    db.session.commit()


def _marcar(app, texto, parte="teste"):
    with app.test_request_context():
        return str(marcar_termos(texto, parte))


# ---------- Filtro que sublinha os termos ----------

def test_marca_o_termo_com_link_e_explicacao(app, termos):
    html = _marcar(app, "Leve o CPF original.")
    assert '<a class="termo" href="/glossario#cpf"' in html
    assert 'data-explicacao="Cadastro de Pessoas Físicas."' in html
    assert ">CPF</a> original." in html


def test_so_a_primeira_vez_em_cada_parte(app, termos):
    with app.test_request_context():
        primeira = str(marcar_termos("CPF e CPF de novo", "o_que_e"))
        mesma_parte = str(marcar_termos("Outro parágrafo com CPF", "o_que_e"))
        outra_parte = str(marcar_termos("CPF na lista", "quem_tem_direito"))
    assert primeira.count('class="termo"') == 1
    assert 'class="termo"' not in mesma_parte
    assert outra_parte.count('class="termo"') == 1


def test_termo_maior_ganha_e_palavra_inteira(app, termos):
    html = _marcar(app, "Faça o Cadastro Único. Os CPFs não contam.")
    assert ">Cadastro Único</a>" in html
    assert "/glossario#cadastro\"" not in html   # não marcou só "Cadastro"
    assert "CPFs" in html and ">CPF</a>" not in html


def test_ignora_maiusculas_e_mantem_o_texto_original(app, termos):
    html = _marcar(app, "Entre na Conta GOV.BR pelo celular.")
    assert ">Conta GOV.BR</a>" in html
    assert 'href="/glossario#conta-gov-br"' in html


def test_texto_e_escapado(app, termos):
    html = _marcar(app, '<script>alert(1)</script> CPF & "aspas"')
    assert "<script>" not in html
    assert "&lt;script&gt;" in html and "&amp;" in html
    assert 'class="termo"' in html


def test_explicacao_com_aspas_nao_quebra_o_atributo(app):
    db.session.add(TermoGlossario(termo="Pix", explicacao='Pedido de Pix para "taxa" é golpe.'))
    db.session.commit()
    html = _marcar(app, "Não pague Pix.")
    assert 'data-explicacao="Pedido de Pix para &#34;taxa&#34; é golpe."' in html


def test_sem_termos_devolve_o_texto(app):
    assert _marcar(app, "Texto <b>simples</b>") == "Texto &lt;b&gt;simples&lt;/b&gt;"


def test_termos_carregados_uma_vez_por_pagina(app, termos):
    with app.test_request_context():
        marcar_termos("CPF", "a")
        carregados = g.glossario
        marcar_termos("CPF", "b")
        assert g.glossario is carregados


# ---------- Página do conteúdo ----------

def test_pagina_do_conteudo_sublinha_so_os_textos(cliente, termos):
    cnh = Conteudo.query.filter_by(slug="primeira-habilitacao-cnh").one()
    cnh.o_que_e = "A CNH pede CPF."
    db.session.commit()
    html = cliente.get("/conteudo/primeira-habilitacao-cnh").get_data(as_text=True)
    assert html.count('class="termo"') == 1          # só no "O que é"
    assert "<span>CPF</span>" in html or "CPF</li>" in html  # checklist sem link


# ---------- Página pública /glossario ----------

def test_pagina_do_glossario_em_ordem_alfabetica(cliente, termos):
    html = cliente.get("/glossario").get_data(as_text=True)
    assert 'id="cpf"' in html and 'id="cadastro-unico"' in html
    assert html.index("Cadastro Único") < html.index("conta gov.br") < html.index("Cadastro de Pessoas")
    assert "/glossario" in cliente.get("/").get_data(as_text=True)  # link no rodapé


def test_pagina_do_glossario_vazia(cliente):
    assert "Ainda não há termos" in cliente.get("/glossario").get_data(as_text=True)


# ---------- Cadastro no admin ----------

def test_glossario_do_admin_exige_login(cliente):
    resposta = cliente.get("/admin/glossario")
    assert resposta.status_code == 302 and "/admin/login" in resposta.headers["Location"]


def test_admin_cria_edita_e_exclui_termo(admin_logado):
    cliente = admin_logado
    resposta = cliente.post("/admin/glossario/novo",
                            data={"termo": " INSS ", "explicacao": "Instituto Nacional do Seguro Social."})
    assert resposta.headers["Location"].endswith("/admin/glossario")
    termo = TermoGlossario.query.one()
    assert termo.termo == "INSS"

    cliente.post(f"/admin/glossario/{termo.id}/editar",
                 data={"termo": "INSS", "explicacao": "Cuida da aposentadoria."})
    assert db.session.get(TermoGlossario, termo.id).explicacao == "Cuida da aposentadoria."
    assert "INSS" in cliente.get("/admin/glossario").get_data(as_text=True)

    cliente.post(f"/admin/glossario/{termo.id}/excluir")
    assert TermoGlossario.query.count() == 0


def test_admin_nao_repete_termo(admin_logado, termos):
    html = admin_logado.post("/admin/glossario/novo",
                             data={"termo": "cpf", "explicacao": "Outra explicação."}).get_data(as_text=True)
    assert "já está no glossário" in html
    assert TermoGlossario.query.filter_by(termo="cpf").count() == 0


def test_admin_explicacao_limitada(admin_logado):
    html = admin_logado.post("/admin/glossario/novo",
                             data={"termo": "Teste", "explicacao": "x" * 401}).get_data(as_text=True)
    assert "no máximo 400 caracteres" in html
    assert TermoGlossario.query.count() == 0
