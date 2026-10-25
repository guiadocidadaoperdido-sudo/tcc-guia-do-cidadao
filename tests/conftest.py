import os
import sys

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import create_app  # noqa: E402
from app.extensions import db  # noqa: E402
from app.models import Administrador, Categoria, Conteudo, FonteOficial  # noqa: E402
from config import ConfigTeste  # noqa: E402

EMAIL_ADMIN = "admin@exemplo.com.br"
SENHA_ADMIN = "senha-de-teste-123"
EMAIL = "maria@exemplo.com.br"
SENHA = "senha-da-maria"


@pytest.fixture
def app():
    app = create_app(ConfigTeste)
    with app.app_context():
        db.create_all()
        _popular()
        yield app
        db.session.remove()
        db.drop_all()


def _popular():
    admin = Administrador(nome="Admin Teste", email=EMAIL_ADMIN)
    admin.definir_senha(SENHA_ADMIN)
    transito = Categoria(nome="Trânsito e habilitação", slug="transito-e-habilitacao")
    moradia = Categoria(nome="Moradia", slug="moradia")
    vazia = Categoria(nome="Educação", slug="educacao")

    cnh = Conteudo(
        categoria=transito,
        titulo="Primeira habilitação (CNH)",
        slug="primeira-habilitacao-cnh",
        resumo="Como tirar a primeira CNH.",
        o_que_e="A CNH é o documento que permite dirigir.",
        quem_tem_direito="Ter 18 anos\nSaber ler e escrever",
        documentos="Documento de identidade com foto\nCPF",
        como_solicitar="Abra o processo\nFaça as provas",
        alerta_golpes="Não pague taxas em sites desconhecidos.",
        publicado=True,
    )
    cnh.fontes = [FonteOficial(orgao="Ministério dos Transportes", titulo="CNH do Brasil",
                               url="https://www.gov.br/transportes/pt-br/cnh-do-brasil")]

    rascunho = Conteudo(
        categoria=moradia,
        titulo="Minha Casa, Minha Vida",
        slug="minha-casa-minha-vida",
        resumo="Programa de moradia.",
        o_que_e="Programa habitacional.",
        publicado=False,
    )
    rascunho.fontes = [FonteOficial(orgao="Ministério das Cidades", titulo="MCMV",
                                    url="https://www.gov.br/cidades")]
    db.session.add_all([admin, transito, moradia, vazia, cnh, rascunho])
    db.session.commit()


@pytest.fixture
def cliente(app):
    return app.test_client()


@pytest.fixture
def admin_logado(cliente):
    cliente.post("/admin/login", data={"email": EMAIL_ADMIN, "senha": SENHA_ADMIN})
    return cliente


def _cadastrar(cliente, email=EMAIL, senha=SENHA, confirmar=None, consentimento="y"):
    """Cria uma conta de cidadão (e já entra nela)."""
    dados = {"email": email, "senha": senha, "confirmar_senha": confirmar or senha}
    if consentimento:
        dados["consentimento"] = consentimento
    return cliente.post("/conta/cadastrar", data=dados)


@pytest.fixture
def cidadao_logado(cliente):
    _cadastrar(cliente)
    return cliente
