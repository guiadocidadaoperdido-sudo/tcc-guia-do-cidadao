"""Testes das funções acrescentadas no MVP: API, PWA, saúde, limite de
tentativas, relacionados, checklist e migrações."""
import pytest

from app import create_app
from app.extensions import db
from config import ConfigTeste

from conftest import EMAIL_ADMIN, _popular


# ---------- API REST (somente leitura) ----------

def test_api_lista_so_conteudos_publicados(cliente):
    dados = cliente.get("/api/v1/conteudos").get_json()
    slugs = [c["slug"] for c in dados["conteudos"]]
    assert "primeira-habilitacao-cnh" in slugs
    assert "minha-casa-minha-vida" not in slugs  # rascunho não aparece
    assert dados["total"] == len(slugs)


def test_api_busca_e_filtro_por_categoria(cliente):
    assert cliente.get("/api/v1/conteudos?q=CNH").get_json()["total"] == 1
    assert cliente.get("/api/v1/conteudos?q=xyzabc").get_json()["total"] == 0
    assert cliente.get("/api/v1/conteudos?categoria=moradia").get_json()["total"] == 0


def test_api_detalhe_traz_partes_e_fontes(cliente):
    dados = cliente.get("/api/v1/conteudos/primeira-habilitacao-cnh").get_json()
    assert dados["documentos"] == ["Documento de identidade com foto", "CPF"]
    assert dados["fontes"][0]["url"].startswith("https://www.gov.br/")
    assert "senha_hash" not in str(dados)


def test_api_rascunho_e_inexistente_dao_404_em_json(cliente):
    for slug in ("minha-casa-minha-vida", "nao-existe"):
        resposta = cliente.get(f"/api/v1/conteudos/{slug}")
        assert resposta.status_code == 404
        assert resposta.get_json()["erro"]


def test_api_categorias(cliente):
    dados = cliente.get("/api/v1/categorias").get_json()
    assert {c["slug"] for c in dados["categorias"]} >= {"moradia", "transito-e-habilitacao"}


# ---------- Saúde, PWA e páginas de apoio ----------

def test_saude_confere_o_banco(cliente):
    resposta = cliente.get("/saude")
    assert resposta.status_code == 200
    assert resposta.get_json() == {"status": "ok", "banco": "ok"}


def test_service_worker_na_raiz_e_manifest(cliente):
    sw = cliente.get("/sw.js")
    assert sw.status_code == 200
    assert "javascript" in sw.headers["Content-Type"]
    assert cliente.get("/static/manifest.webmanifest").status_code == 200
    assert cliente.get("/offline").status_code == 200


def test_csp_sem_servicos_de_terceiros(cliente):
    csp = cliente.get("/").headers["Content-Security-Policy"]
    assert "googleapis" not in csp and "gstatic" not in csp


# ---------- Página do conteúdo ----------

def test_conteudo_tem_checklist_e_relacionados(app, cliente):
    from app.models import Categoria, Conteudo, FonteOficial
    cat = Categoria.query.filter_by(slug="transito-e-habilitacao").first()
    outro = Conteudo(categoria=cat, titulo="Renovar a CNH", slug="renovar-cnh",
                     resumo="Como renovar.", o_que_e="Renovação.", publicado=True)
    outro.fontes = [FonteOficial(orgao="Senatran", titulo="CNH", url="https://www.gov.br")]
    db.session.add(outro)
    db.session.commit()

    html = cliente.get("/conteudo/primeira-habilitacao-cnh").get_data(as_text=True)
    assert 'data-checklist="primeira-habilitacao-cnh"' in html
    assert html.count('type="checkbox"') == 2
    assert "Veja também" in html and "/conteudo/renovar-cnh" in html


# ---------- Limite de tentativas no login ----------

class ConfigComLimite(ConfigTeste):
    RATELIMIT_ENABLED = True
    LIMITE_LOGIN = "3 per minute"


def test_login_bloqueia_depois_de_muitas_tentativas():
    app = create_app(ConfigComLimite)
    with app.app_context():
        db.create_all()
        _popular()
        cliente = app.test_client()
        dados = {"email": EMAIL_ADMIN, "senha": "senha-errada"}
        codigos = [cliente.post("/admin/login", data=dados).status_code for _ in range(4)]
        assert codigos[:3] == [200, 200, 200]
        assert codigos[3] == 429
        # Abrir a tela de login (GET) continua liberado.
        assert cliente.get("/admin/login").status_code == 200
        db.session.remove()
        db.drop_all()


# ---------- Migrações ----------

def test_migracoes_criam_as_cinco_tabelas(tmp_path):
    from flask_migrate import downgrade, upgrade
    from sqlalchemy import inspect

    class ConfigArquivo(ConfigTeste):
        SQLALCHEMY_DATABASE_URI = f"sqlite:///{(tmp_path / 'mig.db').as_posix()}"

    app = create_app(ConfigArquivo)
    with app.app_context():
        upgrade()
        tabelas = set(inspect(db.engine).get_table_names())
        assert {"administrador", "categoria", "conteudo", "fonte_oficial", "avaliacao"} <= tabelas
        downgrade(revision="base")
        assert "conteudo" not in inspect(db.engine).get_table_names()
        db.engine.dispose()


@pytest.mark.parametrize("caminho", ["/", "/busca?q=cnh", "/sobre", "/categoria/moradia"])
def test_paginas_publicas_abrem(cliente, caminho):
    assert cliente.get(caminho).status_code == 200
