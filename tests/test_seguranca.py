"""Testes ligados aos requisitos não funcionais de segurança."""
from app import create_app
from app.extensions import db
from app.models import Administrador
from config import ConfigTeste


def test_rnf04_senha_guardada_como_hash(app):
    admin = Administrador.query.first()
    assert admin.senha_hash != "senha-de-teste-123"
    assert admin.conferir_senha("senha-de-teste-123")


def test_rnf05_busca_com_aspas_nao_quebra(cliente):
    resposta = cliente.get("/busca?q=' OR 1=1 --")
    assert resposta.status_code == 200


def test_cabecalhos_de_seguranca(cliente):
    resposta = cliente.get("/")
    assert resposta.headers["X-Content-Type-Options"] == "nosniff"
    assert "frame-ancestors 'none'" in resposta.headers["Content-Security-Policy"]


def test_login_nao_redireciona_para_outro_site(cliente):
    resposta = cliente.post("/admin/login?next=https://site-malicioso.com",
                            data={"email": "admin@exemplo.com.br", "senha": "senha-de-teste-123"})
    assert resposta.headers["Location"].endswith("/admin/")


def test_texto_do_conteudo_e_escapado(admin_logado, cliente):
    from app.models import Categoria
    cat = Categoria.query.first()
    admin_logado.post("/admin/conteudos/novo", data={
        "titulo": "Teste XSS", "categoria_id": cat.id, "resumo": "r",
        "o_que_e": "<script>alert(1)</script>", "publicado": "y",
        "fonte_orgao": ["Órgão"], "fonte_titulo": ["T"], "fonte_url": ["https://www.gov.br"],
    })
    html = cliente.get("/conteudo/teste-xss").get_data(as_text=True)
    assert "<script>alert(1)</script>" not in html
    assert "&lt;script&gt;" in html


class ConfigComCsrf(ConfigTeste):
    WTF_CSRF_ENABLED = True


def test_rnf06_formulario_sem_token_csrf_e_recusado():
    app = create_app(ConfigComCsrf)
    with app.app_context():
        db.create_all()
        resposta = app.test_client().post("/admin/login", data={"email": "a@b.com", "senha": "x"})
        assert resposta.status_code == 400
        db.drop_all()
