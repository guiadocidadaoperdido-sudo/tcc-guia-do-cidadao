"""Blueprint da área administrativa. Todas as rotas, menos o login, exigem login (RF08)."""
from datetime import datetime
from urllib.parse import urlsplit

from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user
from sqlalchemy import func

from ..extensions import db
from ..forms import CategoriaForm, ConteudoForm, LoginForm
from ..models import Administrador, Avaliacao, Categoria, Conteudo, FonteOficial
from ..utils import gerar_slug, url_segura

bp = Blueprint("admin", __name__)


@bp.before_request
def exigir_login():
    if request.endpoint in ("admin.login",):
        return None
    if not current_user.is_authenticated:
        from ..extensions import login_manager
        return login_manager.unauthorized()
    return None


@bp.after_request
def sem_cache(resposta):
    # Páginas da área restrita não ficam guardadas no navegador.
    resposta.headers["Cache-Control"] = "no-store"
    return resposta


# ---------- Login (RF08) ----------

def _destino_seguro(destino):
    """Só aceita redirecionar para um endereço deste mesmo site."""
    if not destino:
        return None
    partes = urlsplit(destino)
    if partes.scheme or partes.netloc or not destino.startswith("/"):
        return None
    return destino


@bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("admin.painel"))
    form = LoginForm()
    if form.validate_on_submit():
        email = form.email.data.strip().lower()
        admin = Administrador.query.filter(func.lower(Administrador.email) == email).first()
        if admin and admin.conferir_senha(form.senha.data):
            login_user(admin)
            flash(f"Olá, {admin.nome}!", "sucesso")
            return redirect(_destino_seguro(request.args.get("next")) or url_for("admin.painel"))
        # Mesma mensagem para e-mail e senha errados, para não revelar qual falhou.
        flash("E-mail ou senha incorretos.", "erro")
    return render_template("admin/login.html", form=form)


@bp.route("/sair", methods=["POST"])
def sair():
    logout_user()
    flash("Você saiu da área administrativa.", "sucesso")
    return redirect(url_for("admin.login"))


@bp.route("/")
def painel():
    totais = {
        "categorias": Categoria.query.count(),
        "conteudos": Conteudo.query.count(),
        "publicados": Conteudo.query.filter_by(publicado=True).count(),
        "avaliacoes": Avaliacao.query.count(),
    }
    ultimos = Conteudo.query.order_by(Conteudo.atualizado_em.desc()).limit(5).all()
    return render_template("admin/painel.html", totais=totais, ultimos=ultimos)


# ---------- Categorias (RF10) ----------

@bp.route("/categorias")
def categorias():
    lista = Categoria.query.order_by(Categoria.nome).all()
    return render_template("admin/categorias.html", categorias=lista)


@bp.route("/categorias/nova", methods=["GET", "POST"])
@bp.route("/categorias/<int:id>/editar", methods=["GET", "POST"])
def categoria_form(id=None):
    categoria = db.session.get(Categoria, id) if id else Categoria()
    if categoria is None:
        abort(404)
    form = CategoriaForm(obj=categoria)
    if form.validate_on_submit():
        slug = form.slug.data or gerar_slug(form.nome.data)
        repetida = Categoria.query.filter(Categoria.slug == slug, Categoria.id != (id or 0)).first()
        if not slug:
            form.slug.errors.append("Não foi possível gerar o endereço. Preencha o campo.")
        elif repetida:
            form.slug.errors.append("Já existe uma categoria com esse endereço.")
        else:
            categoria.nome = form.nome.data.strip()
            categoria.slug = slug
            categoria.descricao = (form.descricao.data or "").strip() or None
            if not id:
                db.session.add(categoria)
            db.session.commit()
            flash("Categoria salva.", "sucesso")
            return redirect(url_for("admin.categorias"))
    return render_template("admin/categoria_form.html", form=form, categoria=categoria)


@bp.route("/categorias/<int:id>/excluir", methods=["POST"])
def categoria_excluir(id):
    categoria = db.get_or_404(Categoria, id)
    # CT11: não deixa apagar uma categoria que ainda tem conteúdos.
    if categoria.conteudos:
        flash(
            f"A categoria \"{categoria.nome}\" tem {len(categoria.conteudos)} conteúdo(s). "
            "Mova ou exclua os conteúdos antes de excluir a categoria.",
            "erro",
        )
        return redirect(url_for("admin.categorias"))
    db.session.delete(categoria)
    db.session.commit()
    flash("Categoria excluída.", "sucesso")
    return redirect(url_for("admin.categorias"))


# ---------- Conteúdos e fontes oficiais (RF09 e RF11) ----------

@bp.route("/conteudos")
def conteudos():
    lista = Conteudo.query.order_by(Conteudo.atualizado_em.desc()).all()
    return render_template("admin/conteudos.html", conteudos=lista)


def _ler_fontes():
    """Lê as linhas de fontes oficiais enviadas pelo formulário."""
    orgaos = request.form.getlist("fonte_orgao")
    titulos = request.form.getlist("fonte_titulo")
    urls = request.form.getlist("fonte_url")
    fontes, erros = [], []
    for n, (orgao, titulo, url) in enumerate(zip(orgaos, titulos, urls), start=1):
        orgao, titulo, url = orgao.strip(), titulo.strip(), url.strip()
        if not (orgao or titulo or url):
            continue  # linha vazia: ignorada (é assim que se remove uma fonte)
        if not (orgao and titulo and url):
            erros.append(f"Fonte {n}: preencha órgão, título e endereço.")
        elif not url_segura(url):
            erros.append(f"Fonte {n}: o endereço precisa começar com https:// ou http://.")
        elif len(orgao) > 120 or len(titulo) > 150 or len(url) > 500:
            erros.append(f"Fonte {n}: texto maior que o permitido.")
        fontes.append({"orgao": orgao, "titulo": titulo, "url": url})
    if not fontes:
        # CT09: todo conteúdo precisa de pelo menos uma fonte oficial.
        erros.append("Cadastre pelo menos uma fonte oficial. Todo conteúdo precisa de fonte.")
    return fontes, erros


@bp.route("/conteudos/novo", methods=["GET", "POST"])
@bp.route("/conteudos/<int:id>/editar", methods=["GET", "POST"])
def conteudo_form(id=None):
    conteudo = db.session.get(Conteudo, id) if id else Conteudo()
    if conteudo is None:
        abort(404)
    form = ConteudoForm(obj=conteudo)
    form.categoria_id.choices = [(c.id, c.nome) for c in Categoria.query.order_by(Categoria.nome)]
    if not form.categoria_id.choices:
        flash("Cadastre uma categoria antes de criar conteúdos.", "aviso")
        return redirect(url_for("admin.categoria_form"))

    fontes = [{"orgao": f.orgao, "titulo": f.titulo, "url": f.url} for f in conteudo.fontes]
    erros_fontes = []

    if request.method == "POST":
        fontes, erros_fontes = _ler_fontes()
        if form.validate_on_submit() and not erros_fontes:
            slug = form.slug.data or gerar_slug(form.titulo.data)
            repetido = Conteudo.query.filter(Conteudo.slug == slug, Conteudo.id != (id or 0)).first()
            if not slug:
                form.slug.errors.append("Não foi possível gerar o endereço. Preencha o campo.")
            elif repetido:
                form.slug.errors.append("Já existe um conteúdo com esse endereço.")
            else:
                form.populate_obj(conteudo)
                conteudo.slug = slug
                for campo in ("quem_tem_direito", "documentos", "como_solicitar", "alerta_golpes"):
                    valor = (getattr(conteudo, campo) or "").strip()
                    setattr(conteudo, campo, valor or None)
                conteudo.administrador_id = current_user.id
                conteudo.atualizado_em = datetime.now()
                # Troca a lista de fontes pela que veio do formulário (RF11).
                conteudo.fontes = [FonteOficial(**f) for f in fontes]
                if not id:
                    db.session.add(conteudo)
                db.session.commit()
                estado = "publicado" if conteudo.publicado else "salvo como rascunho"
                flash(f"Conteúdo {estado}.", "sucesso")
                return redirect(url_for("admin.conteudos"))

    if not fontes:
        fontes = [{"orgao": "", "titulo": "", "url": ""}]
    return render_template(
        "admin/conteudo_form.html",
        form=form, conteudo=conteudo, fontes=fontes, erros_fontes=erros_fontes,
    )


@bp.route("/conteudos/<int:id>/publicar", methods=["POST"])
def conteudo_publicar(id):
    conteudo = db.get_or_404(Conteudo, id)
    if not conteudo.publicado and not conteudo.fontes:
        flash("Este conteúdo não tem fonte oficial. Cadastre uma antes de publicar.", "erro")
        return redirect(url_for("admin.conteudos"))
    conteudo.publicado = not conteudo.publicado
    conteudo.administrador_id = current_user.id
    db.session.commit()
    flash("Conteúdo publicado." if conteudo.publicado else "Conteúdo retirado do site.", "sucesso")
    return redirect(url_for("admin.conteudos"))


@bp.route("/conteudos/<int:id>/excluir", methods=["POST"])
def conteudo_excluir(id):
    conteudo = db.get_or_404(Conteudo, id)
    db.session.delete(conteudo)
    db.session.commit()
    flash("Conteúdo excluído.", "sucesso")
    return redirect(url_for("admin.conteudos"))


# ---------- Avaliações (RF12) ----------

@bp.route("/avaliacoes")
def avaliacoes():
    sim = func.count(Avaliacao.id).filter(Avaliacao.util.is_(True))
    nao = func.count(Avaliacao.id).filter(Avaliacao.util.is_(False))
    linhas = (
        db.session.query(Conteudo, sim.label("sim"), nao.label("nao"))
        .outerjoin(Avaliacao, Avaliacao.conteudo_id == Conteudo.id)
        .group_by(Conteudo.id)
        .order_by(Conteudo.titulo)
        .all()
    )
    comentarios = (
        Avaliacao.query.filter(Avaliacao.comentario.isnot(None))
        .order_by(Avaliacao.criado_em.desc())
        .limit(20)
        .all()
    )
    return render_template("admin/avaliacoes.html", linhas=linhas, comentarios=comentarios)
