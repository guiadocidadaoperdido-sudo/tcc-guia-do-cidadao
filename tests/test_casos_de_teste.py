"""Casos de teste funcionais do Quadro 8 do TCC (CT01 a CT12)."""
from app.extensions import db
from app.models import Avaliacao, Categoria, Conteudo


def texto(resposta):
    return resposta.get_data(as_text=True)


def test_ct01_pagina_inicial_mostra_categorias(cliente):
    resposta = cliente.get("/")
    assert resposta.status_code == 200
    assert "Trânsito e habilitação" in texto(resposta)
    assert "Moradia" in texto(resposta)


def test_ct02_buscar_cnh(cliente):
    resposta = cliente.get("/busca?q=CNH")
    assert resposta.status_code == 200
    assert "Primeira habilitação (CNH)" in texto(resposta)


def test_ct03_buscar_palavra_inexistente(cliente):
    resposta = cliente.get("/busca?q=xyzabc")
    html = texto(resposta)
    assert "Não encontramos nada" in html
    assert "/categoria/moradia" in html  # sugestão de temas


def test_ct04_abrir_conteudo_publicado(cliente):
    html = texto(cliente.get("/conteudo/primeira-habilitacao-cnh"))
    for parte in ("O que é", "Quem tem direito", "Documentos necessários", "Como solicitar"):
        assert parte in html
    assert "Atenção aos golpes" in html
    assert "https://www.gov.br/transportes/pt-br/cnh-do-brasil" in html
    assert "Atualizado em" in html


def test_ct05_conteudo_nao_publicado_da_404(cliente):
    assert cliente.get("/conteudo/minha-casa-minha-vida").status_code == 404


def test_ct06_avaliar_sim(cliente, app):
    resposta = cliente.post("/conteudo/primeira-habilitacao-cnh/avaliar",
                            data={"util": "sim"}, follow_redirects=True)
    assert "Obrigado pela sua resposta" in texto(resposta)
    assert Avaliacao.query.filter_by(util=True).count() == 1


def test_ct06_avaliacao_repetida_nao_conta_duas_vezes(cliente):
    for _ in range(3):
        cliente.post("/conteudo/primeira-habilitacao-cnh/avaliar", data={"util": "sim"})
    assert Avaliacao.query.count() == 1


def test_ct07_login_com_senha_errada(cliente):
    resposta = cliente.post("/admin/login", data={"email": "admin@exemplo.com.br", "senha": "errada"},
                            follow_redirects=True)
    assert "E-mail ou senha incorretos" in texto(resposta)
    assert cliente.get("/admin/").status_code == 302


def test_ct08_area_admin_sem_login_vai_para_login(cliente):
    resposta = cliente.get("/admin/conteudos")
    assert resposta.status_code == 302
    assert "/admin/login" in resposta.headers["Location"]


def _dados_conteudo(**extra):
    dados = {
        "titulo": "Seguro-desemprego",
        "slug": "",
        "categoria_id": Categoria.query.filter_by(slug="moradia").first().id,
        "resumo": "Resumo do seguro-desemprego.",
        "o_que_e": "É um benefício para quem foi demitido sem justa causa.",
        "publicado": "y",
        "fonte_orgao": [""],
        "fonte_titulo": [""],
        "fonte_url": [""],
    }
    dados.update(extra)
    return dados


def test_ct09_salvar_conteudo_sem_fonte(admin_logado):
    resposta = admin_logado.post("/admin/conteudos/novo", data=_dados_conteudo())
    assert resposta.status_code == 200
    assert "pelo menos uma fonte oficial" in texto(resposta)
    assert Conteudo.query.filter_by(slug="seguro-desemprego").first() is None


def test_ct09_fonte_com_endereco_invalido(admin_logado):
    dados = _dados_conteudo(fonte_orgao=["MTE"], fonte_titulo=["Seguro"], fonte_url=["javascript:alert(1)"])
    resposta = admin_logado.post("/admin/conteudos/novo", data=dados)
    assert "https://" in texto(resposta)
    assert Conteudo.query.filter_by(slug="seguro-desemprego").first() is None


def test_ct10_publicar_conteudo(admin_logado, cliente):
    rascunho = Conteudo.query.filter_by(slug="minha-casa-minha-vida").first()
    admin_logado.post(f"/admin/conteudos/{rascunho.id}/publicar")
    html = texto(cliente.get("/categoria/moradia"))
    assert "Minha Casa, Minha Vida" in html
    assert cliente.get("/conteudo/minha-casa-minha-vida").status_code == 200


def test_ct10_criar_conteudo_com_fonte_e_publicar(admin_logado, cliente):
    dados = _dados_conteudo(fonte_orgao=["Ministério do Trabalho"], fonte_titulo=["Seguro-desemprego"],
                            fonte_url=["https://www.gov.br/trabalho-e-emprego"])
    resposta = admin_logado.post("/admin/conteudos/novo", data=dados)
    assert resposta.status_code == 302
    novo = Conteudo.query.filter_by(slug="seguro-desemprego").first()
    assert novo.publicado and len(novo.fontes) == 1
    assert novo.administrador.email == "admin@exemplo.com.br"
    assert cliente.get("/conteudo/seguro-desemprego").status_code == 200


def test_ct11_excluir_categoria_com_conteudos(admin_logado):
    cat = Categoria.query.filter_by(slug="transito-e-habilitacao").first()
    resposta = admin_logado.post(f"/admin/categorias/{cat.id}/excluir", follow_redirects=True)
    assert "Mova ou exclua os conteúdos" in texto(resposta)
    assert db.session.get(Categoria, cat.id) is not None


def test_ct11_excluir_categoria_vazia(admin_logado):
    cat = Categoria.query.filter_by(slug="educacao").first()
    admin_logado.post(f"/admin/categorias/{cat.id}/excluir")
    assert db.session.get(Categoria, cat.id) is None


def test_ct12_tela_de_avaliacoes(admin_logado, cliente, app):
    conteudo = Conteudo.query.filter_by(slug="primeira-habilitacao-cnh").first()
    db.session.add_all([Avaliacao(conteudo_id=conteudo.id, util=True),
                        Avaliacao(conteudo_id=conteudo.id, util=True),
                        Avaliacao(conteudo_id=conteudo.id, util=False)])
    db.session.commit()
    html = texto(admin_logado.get("/admin/avaliacoes"))
    assert "Primeira habilitação (CNH)" in html
    assert "<td>2</td>" in html and "<td>1</td>" in html and "67%" in html


def test_busca_em_portugues_acha_plural(cliente):
    """No PostgreSQL, buscar "documentos" encontra o texto que usa "documento"."""
    import pytest
    if db.engine.dialect.name != "postgresql":
        pytest.skip("A pesquisa de texto em português só existe no PostgreSQL.")
    html = texto(cliente.get("/busca?q=documentos"))
    assert "Primeira habilitação (CNH)" in html
