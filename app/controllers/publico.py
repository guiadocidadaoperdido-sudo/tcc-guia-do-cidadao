"""Blueprint da parte pública: o visitante não precisa fazer login."""
from flask import (
    Blueprint, abort, current_app, flash, jsonify, make_response, redirect, render_template,
    request, send_from_directory, session, url_for,
)
from sqlalchemy import text

from ..extensions import db, limiter
from ..forms import DenunciaForm, VerificadorForm
from ..models import Avaliacao, Categoria, Conteudo, LinkDenunciado
from ..models.link_denunciado import CONFIRMADO
from ..utils import hoje
from ..verificador import verificar
from .conta import cidadao_atual, registrar_visita

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

    # Meu acompanhamento: só existe para quem entrou na conta e salvou o tema.
    usuario = cidadao_atual()
    acompanhamento, visto_antes = registrar_visita(usuario, item)

    resposta = make_response(render_template(
        "publico/conteudo.html", conteudo=item, ja_avaliou=ja_avaliou,
        relacionados=_relacionados(item), acompanhamento=acompanhamento,
        visto_antes=visto_antes, hoje=hoje(),
    ))
    if usuario:
        # Com a pessoa logada a página mostra o andamento dela: não guarda no
        # navegador nem no modo offline (computador compartilhado).
        resposta.headers["Cache-Control"] = "no-store"
    return resposta


def _relacionados(item, limite=3):
    """Outros conteúdos do mesmo tema; se faltar, completa com os mais recentes."""
    publicados = Conteudo.query.filter(Conteudo.publicado.is_(True), Conteudo.id != item.id)
    lista = (
        publicados.filter(Conteudo.categoria_id == item.categoria_id)
        .order_by(Conteudo.titulo).limit(limite).all()
    )
    if len(lista) < limite:
        if lista:
            publicados = publicados.filter(Conteudo.id.notin_([c.id for c in lista]))
        lista += (
            publicados.order_by(Conteudo.atualizado_em.desc())
            .limit(limite - len(lista)).all()
        )
    return lista


@bp.route("/conteudo/<slug>/avaliar", methods=["POST"])
@limiter.limit(lambda: current_app.config["LIMITE_AVALIACAO"])
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


@bp.route("/verificar-golpe", methods=["GET", "POST"])
@limiter.limit(lambda: current_app.config["LIMITE_VERIFICADOR"], methods=["POST"])
def verificar_golpe():
    """Verificador de golpe, aberto a todos (sem conta).

    Usa POST para o texto não aparecer no endereço nem no histórico. Nada do
    que a pessoa cola é guardado no banco ou no log (RNF10).
    """
    form = VerificadorForm()
    resultado = None
    if form.validate_on_submit():
        confirmados = db.session.query(LinkDenunciado.dominio).filter_by(
            status=CONFIRMADO).distinct()
        resultado = verificar(form.texto.data, denunciados=[d for (d,) in confirmados])
    resposta = make_response(render_template(
        "publico/verificar_golpe.html", form=form, resultado=resultado,
        form_denuncia=DenunciaForm(formdata=None),
    ))
    # O resultado mostra o que a pessoa colou: não fica guardado no navegador.
    resposta.headers["Cache-Control"] = "no-store"
    return resposta


@bp.route("/sobre")
def sobre():
    return render_template("publico/sobre.html")


@bp.route("/offline")
def offline():
    # Página mostrada pelo aplicativo (PWA) quando o celular está sem internet.
    return render_template("publico/offline.html")


@bp.route("/sw.js")
def service_worker():
    # O service worker precisa ser servido na raiz para valer para o site todo.
    resposta = send_from_directory(current_app.static_folder, "js/sw.js")
    resposta.headers["Cache-Control"] = "no-cache"
    resposta.headers["Content-Type"] = "text/javascript; charset=utf-8"
    return resposta


@bp.route("/saude")
def saude():
    """Verificação de saúde usada pelo Render: o site e o banco respondem?"""
    try:
        db.session.execute(text("SELECT 1"))
        return jsonify(status="ok", banco="ok")
    except Exception:  # noqa: BLE001
        current_app.logger.exception("Falha ao acessar o banco na verificação de saúde")
        return jsonify(status="erro", banco="indisponível"), 503
