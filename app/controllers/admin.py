"""Blueprint da área administrativa. Todas as rotas, menos o login, exigem login (RF08)."""
from datetime import datetime
from urllib.parse import urlsplit

from flask import Blueprint, abort, current_app, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user
from sqlalchemy import func

from ..extensions import db, limiter
from ..forms import BloqueioForm, CategoriaForm, ConteudoForm, LoginForm
from ..models import (
    Administrador, Avaliacao, Categoria, Conteudo, FonteOficial, LinkDenunciado, Usuario,
)
from ..models.link_denunciado import CONFIRMADO, DESCARTADO, PENDENTE
from ..models.usuario import ATIVO, BLOQUEADO, EXCLUIDO
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


def _registrar(acao, *args):
    """Registra no log uma ação da área administrativa, com o e-mail de quem fez."""
    quem = current_user.email if current_user.is_authenticated else "-"
    current_app.logger.info("[admin %s] " + acao, quem, *args)


@bp.route("/login", methods=["GET", "POST"])
# Limite de tentativas por IP contra adivinhação de senha (força bruta).
@limiter.limit(lambda: current_app.config["LIMITE_LOGIN"], methods=["POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("admin.painel"))
    form = LoginForm()
    if form.validate_on_submit():
        email = form.email.data.strip().lower()
        admin = Administrador.query.filter(func.lower(Administrador.email) == email).first()
        if admin and admin.conferir_senha(form.senha.data):
            login_user(admin)
            _registrar("entrou na área administrativa")
            flash(f"Olá, {admin.nome}!", "sucesso")
            return redirect(_destino_seguro(request.args.get("next")) or url_for("admin.painel"))
        # Mesma mensagem para e-mail e senha errados, para não revelar qual falhou.
        current_app.logger.warning("Tentativa de login recusada.")
        flash("E-mail ou senha incorretos.", "erro")
    return render_template("admin/login.html", form=form)


@bp.route("/sair", methods=["POST"])
def sair():
    _registrar("saiu da área administrativa")
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
            _registrar("salvou a categoria %s", categoria.slug)
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
    _registrar("excluiu a categoria %s", categoria.slug)
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
                _registrar("salvou o conteúdo %s", conteudo.slug)
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
    _registrar("%s o conteúdo %s", "publicou" if conteudo.publicado else "despublicou", conteudo.slug)
    flash("Conteúdo publicado." if conteudo.publicado else "Conteúdo retirado do site.", "sucesso")
    return redirect(url_for("admin.conteudos"))


@bp.route("/conteudos/<int:id>/excluir", methods=["POST"])
def conteudo_excluir(id):
    conteudo = db.get_or_404(Conteudo, id)
    db.session.delete(conteudo)
    db.session.commit()
    _registrar("excluiu o conteúdo %s", conteudo.slug)
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


# ---------- Contas dos cidadãos (mesmo padrão do FacilMed) ----------
#
# Três telas separadas, no mesmo visual:
#   - Contas ativas     /admin/usuarios             -> Bloquear
#   - Contas bloqueadas /admin/usuarios/bloqueadas  -> Desbloquear
#   - Contas excluídas  /admin/usuarios/excluidas   -> só leitura
# "Excluída" é quando o próprio cidadão apagou a conta (LGPD): os dados
# pessoais já foram apagados e a conta não volta.

SITUACOES = {
    # situação: (status no banco, endpoint, título, subtítulo)
    "ativas": (ATIVO, "admin.usuarios", "Contas ativas",
               "Quem pode entrar na conta do guia. Bloqueie quem não deve mais acessar."),
    "bloqueadas": (BLOQUEADO, "admin.contas_bloqueadas", "Contas bloqueadas",
                   "Contas que não entram mais. O motivo é interno: a pessoa só vê que a "
                   "conta está bloqueada."),
    "excluidas": (EXCLUIDO, "admin.contas_excluidas", "Contas excluídas",
                  "Contas que o próprio cidadão excluiu (LGPD). Os dados pessoais já foram "
                  "apagados e a conta não volta."),
}
CONTAS_POR_PAGINA = 25


def _listar_contas(situacao):
    status, _, titulo, subtitulo = SITUACOES[situacao]
    busca = request.args.get("busca", "").strip()[:100]

    contagem = dict(
        db.session.query(Usuario.status, func.count(Usuario.id)).group_by(Usuario.status).all()
    )
    consulta = Usuario.query.filter(Usuario.status == status)
    if busca and situacao != "excluidas":  # conta excluída não tem mais e-mail
        consulta = consulta.filter(Usuario.email.ilike(f"%{busca}%"))
    ordem = {
        "ativas": Usuario.criado_em.desc(),
        "bloqueadas": Usuario.bloqueado_em.desc(),
        "excluidas": Usuario.excluida_em.desc(),
    }[situacao]
    pagina = consulta.order_by(ordem, Usuario.id.desc()).paginate(
        per_page=CONTAS_POR_PAGINA, error_out=False
    )

    return render_template(
        "admin/usuarios.html",
        situacao=situacao, situacoes=SITUACOES, titulo=titulo, subtitulo=subtitulo,
        contagem={chave: contagem.get(s[0], 0) for chave, s in SITUACOES.items()},
        pagina=pagina, busca=busca, form_bloqueio=BloqueioForm(),
    )


@bp.route("/usuarios")
def usuarios():
    return _listar_contas("ativas")


@bp.route("/usuarios/bloqueadas")
def contas_bloqueadas():
    return _listar_contas("bloqueadas")


@bp.route("/usuarios/excluidas")
def contas_excluidas():
    return _listar_contas("excluidas")


@bp.route("/usuarios/<int:id>/bloquear", methods=["POST"])
def usuario_bloquear(id):
    """Bloqueio exige motivo: sem registro de quem bloqueou e por quê, ninguém sabe se pode desbloquear."""
    usuario = db.get_or_404(Usuario, id)
    if usuario.status != ATIVO:
        flash("Só dá para bloquear uma conta ativa.", "erro")
        return redirect(url_for("admin.usuarios"))
    form = BloqueioForm()
    if not form.validate_on_submit():
        flash(form.motivo.errors[0] if form.motivo.errors else "Não foi possível bloquear.", "erro")
        return redirect(url_for("admin.usuarios", busca=request.args.get("busca") or None))
    usuario.bloquear(form.motivo.data, current_user)
    db.session.commit()
    # O log guarda o número da conta, não o e-mail do cidadão (RNF10).
    _registrar("bloqueou a conta de cidadão %s", usuario.id)
    flash(f"A conta {usuario.email} foi bloqueada e agora está em Contas bloqueadas.", "sucesso")
    return redirect(url_for("admin.usuarios"))


@bp.route("/usuarios/<int:id>/desbloquear", methods=["POST"])
def usuario_desbloquear(id):
    usuario = db.get_or_404(Usuario, id)
    if usuario.status != BLOQUEADO:
        flash("Essa conta não está bloqueada.", "erro")
        return redirect(url_for("admin.contas_bloqueadas"))
    usuario.desbloquear()
    db.session.commit()
    _registrar("desbloqueou a conta de cidadão %s", usuario.id)
    flash(f"A conta {usuario.email} foi reativada e voltou para Contas ativas.", "sucesso")
    return redirect(url_for("admin.contas_bloqueadas"))


@bp.route("/usuarios/<int:id>/excluir-dados", methods=["POST"])
def usuario_excluir_dados(id):
    """Conta bloqueada não entra mais e não chega ao botão "Excluir minha conta".
    Se a pessoa pedir a exclusão para a equipe (LGPD), o admin faz por aqui."""
    usuario = db.get_or_404(Usuario, id)
    if usuario.status != BLOQUEADO:
        flash("Só contas bloqueadas são excluídas pelo admin. As ativas a própria pessoa exclui.", "erro")
        return redirect(url_for("admin.contas_bloqueadas"))
    usuario.excluir_conta()
    db.session.commit()
    _registrar("excluiu os dados da conta de cidadão %s a pedido do titular", usuario.id)
    flash("Os dados pessoais da conta foram apagados. Ela agora está em Contas excluídas.", "sucesso")
    return redirect(url_for("admin.contas_bloqueadas"))


# ---------- Denúncias de links suspeitos ----------
# Mesmo padrão das contas: três abas (pendentes, confirmadas e descartadas).
# Só os links confirmados entram no verificador de golpe.

SITUACOES_DENUNCIA = {
    # situação: (status no banco, endpoint, título, subtítulo)
    "pendentes": (PENDENTE, "admin.denuncias", "Denúncias pendentes",
                  "Links enviados pelos cidadãos esperando revisão. Não abra o link: "
                  "confira o endereço pelo texto."),
    "confirmadas": (CONFIRMADO, "admin.denuncias_confirmadas", "Golpes confirmados",
                    "Estes domínios fazem o verificador mostrar \"Muito suspeito\" para todo mundo."),
    "descartadas": (DESCARTADO, "admin.denuncias_descartadas", "Denúncias descartadas",
                    "Links que não eram golpe (ou denúncias erradas)."),
}


def _listar_denuncias(situacao):
    status, _, titulo, subtitulo = SITUACOES_DENUNCIA[situacao]
    contagem = dict(
        db.session.query(LinkDenunciado.status, func.count(LinkDenunciado.id))
        .group_by(LinkDenunciado.status).all()
    )
    pagina = (
        LinkDenunciado.query.filter_by(status=status)
        .order_by(LinkDenunciado.criado_em.desc(), LinkDenunciado.id.desc())
        .paginate(per_page=CONTAS_POR_PAGINA, error_out=False)
    )
    return render_template(
        "admin/denuncias.html",
        situacao=situacao, situacoes=SITUACOES_DENUNCIA, titulo=titulo, subtitulo=subtitulo,
        contagem={chave: contagem.get(s[0], 0) for chave, s in SITUACOES_DENUNCIA.items()},
        pagina=pagina,
    )


@bp.route("/denuncias")
def denuncias():
    return _listar_denuncias("pendentes")


@bp.route("/denuncias/confirmadas")
def denuncias_confirmadas():
    return _listar_denuncias("confirmadas")


@bp.route("/denuncias/descartadas")
def denuncias_descartadas():
    return _listar_denuncias("descartadas")


ACOES_DENUNCIA = {
    # ação: (novo status, mensagem)
    "confirmar": (CONFIRMADO, "Golpe confirmado. O domínio {} agora aparece como muito suspeito no verificador."),
    "descartar": (DESCARTADO, "Denúncia de {} descartada."),
    "reabrir": (PENDENTE, "A denúncia de {} voltou para Pendentes."),
}


@bp.route("/denuncias/<int:id>/<acao>", methods=["POST"])
def denuncia_revisar(id, acao):
    if acao not in ACOES_DENUNCIA:
        abort(404)
    denuncia = db.get_or_404(LinkDenunciado, id)
    status, mensagem = ACOES_DENUNCIA[acao]
    # Volta para a aba onde a denúncia estava antes da mudança.
    aba_de_origem = next(s[1] for s in SITUACOES_DENUNCIA.values() if s[0] == denuncia.status)
    denuncia.revisar(status, current_user)
    db.session.commit()
    _registrar("marcou a denúncia %s (%s) como %s", denuncia.id, denuncia.dominio, status)
    flash(mensagem.format(denuncia.dominio), "sucesso")
    return redirect(url_for(aba_de_origem))
