"""API REST somente leitura, em JSON (versão 1).

Entrega os mesmos conteúdos publicados da parte pública, para serem usados
por outros sistemas e pela busca instantânea da própria interface. Não expõe
rascunhos, avaliações nem dados de administradores.
"""
from flask import Blueprint, jsonify, request, url_for

from ..models import Categoria, Conteudo
from ..utils import linhas, paragrafos

bp = Blueprint("api", __name__)

LIMITE_MAXIMO = 50


@bp.after_request
def cache_curto(resposta):
    if resposta.status_code == 200:
        resposta.headers["Cache-Control"] = "public, max-age=300"
    return resposta


def _categoria_json(cat):
    return {
        "nome": cat.nome,
        "slug": cat.slug,
        "descricao": cat.descricao,
        "total_conteudos": len(cat.conteudos_publicados),
        "url": url_for("publico.categoria", slug=cat.slug, _external=True),
    }


def _conteudo_resumo_json(item):
    return {
        "titulo": item.titulo,
        "slug": item.slug,
        "resumo": item.resumo,
        "categoria": {"nome": item.categoria.nome, "slug": item.categoria.slug},
        "atualizado_em": item.atualizado_em.date().isoformat(),
        "url": url_for("publico.conteudo", slug=item.slug, _external=True),
    }


def _conteudo_completo_json(item):
    dados = _conteudo_resumo_json(item)
    dados.update({
        "o_que_e": paragrafos(item.o_que_e),
        "quem_tem_direito": linhas(item.quem_tem_direito),
        "documentos": linhas(item.documentos),
        "como_solicitar": linhas(item.como_solicitar),
        "alerta_golpes": paragrafos(item.alerta_golpes),
        "fontes": [{"orgao": f.orgao, "titulo": f.titulo, "url": f.url} for f in item.fontes],
    })
    return dados


@bp.route("/categorias")
def categorias():
    lista = Categoria.query.order_by(Categoria.nome).all()
    return jsonify(categorias=[_categoria_json(c) for c in lista])


@bp.route("/conteudos")
def conteudos():
    """Lista os conteúdos publicados.

    Parâmetros opcionais: q (busca por palavra), categoria (slug do tema) e
    limite (padrão 20, máximo 50).
    """
    termo = request.args.get("q", "").strip()[:100]
    categoria = request.args.get("categoria", "").strip()
    limite = min(max(request.args.get("limite", 20, type=int), 1), LIMITE_MAXIMO)

    if termo:
        lista = Conteudo.buscar(termo)
    else:
        lista = (
            Conteudo.query.filter_by(publicado=True)
            .order_by(Conteudo.atualizado_em.desc()).all()
        )
    if categoria:
        lista = [c for c in lista if c.categoria.slug == categoria]

    return jsonify(
        total=len(lista),
        conteudos=[_conteudo_resumo_json(c) for c in lista[:limite]],
    )


@bp.route("/conteudos/<slug>")
def conteudo(slug):
    item = Conteudo.query.filter_by(slug=slug, publicado=True).first_or_404()
    return jsonify(_conteudo_completo_json(item))
