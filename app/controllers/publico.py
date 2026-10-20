"""Blueprint da parte pública: o visitante não precisa fazer login."""
from flask import Blueprint, abort, flash, jsonify, redirect, render_template, request, session, url_for

from ..extensions import db
from ..models import Avaliacao, Categoria, Conteudo

bp = Blueprint("publico", __name__)


@bp.route("/")
def inicio():
    # RF01: categorias de temas na página inicial
    categorias = Categoria.query.order_by(Categoria.nome).all()
    recentes = (
        Conteudo.query.filter_by(publicado=True)
        .order_by(Conteudo.atualizado_em.desc())
        .limit(4)
        .all()
    )
    return render_template("publico/inicio.html", categorias=categorias, recentes=recentes)


@bp.route("/categoria/<slug>")
def categoria(slug):
    # RF02: conteúdos publicados de cada categoria
    cat = Categoria.query.filter_by(slug=slug).first_or_404()
    conteudos = (
        Conteudo.query.filter_by(categoria_id=cat.id, publicado=True)
        .order_by(Conteudo.titulo)
        .all()
    )
    return render_template("publico/categoria.html", categoria=cat, conteudos=conteudos)


@bp.route("/busca")
def busca():
    # RF03: busca por palavra-chave
    termo = request.args.get("q", "").strip()[:100]
    resultados = Conteudo.buscar(termo) if termo else []
    categorias = Categoria.query.order_by(Categoria.nome).all()
    return render_template(
        "publico/busca.html", termo=termo, resultados=resultados, categorias=categorias
    )


@bp.route("/conteudo/<slug>")
def conteudo(slug):
    # RF04, RF05 e RF06. Conteúdo não publicado dá erro 404 (CT05).
    item = Conteudo.query.filter_by(slug=slug, publicado=True).first_or_404()
    ja_avaliou = item.id in session.get("avaliados", [])
    return render_template("publico/conteudo.html", conteudo=item, ja_avaliou=ja_avaliou)


@bp.route("/conteudo/<slug>/avaliar", methods=["POST"])
def avaliar(slug):
    # RF07: o visitante diz se o conteúdo foi útil, sem cadastro
    item = Conteudo.query.filter_by(slug=slug, publicado=True).first_or_404()
    resposta = request.form.get("util")
    if resposta not in ("sim", "nao"):
        abort(400)

    avaliados = session.get("avaliados", [])
    if item.id not in avaliados:
        comentario = request.form.get("comentario", "").strip()[:500] or None
        db.session.add(Avaliacao(conteudo_id=item.id, util=resposta == "sim", comentario=comentario))
        db.session.commit()
        # Guarda só o número do conteúdo no cookie de sessão, para evitar votos
        # repetidos. Nenhum dado pessoal é coletado (RNF10).
        session["avaliados"] = avaliados + [item.id]

    mensagem = "Obrigado pela sua resposta! Ela nos ajuda a melhorar o guia."
    if request.headers.get("X-Requested-With") == "fetch":
        return jsonify(ok=True, mensagem=mensagem)
    flash(mensagem, "sucesso")
    return redirect(url_for("publico.conteudo", slug=slug) + "#avaliacao")


@bp.route("/sobre")
def sobre():
    return render_template("publico/sobre.html")
