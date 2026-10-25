"""Blueprint da conta do cidadão (login opcional).

O site continua funcionando sem conta. Quem cria uma conta pode salvar temas,
acompanhar o passo a passo e criar lembretes.

O login do cidadão é separado do login do administrador: o cidadão fica em
session["cidadao_id"] e o administrador continua no Flask-Login. A sessão
acaba quando o navegador é fechado.
"""
from datetime import datetime
from functools import wraps

from flask import (
    Blueprint, Response, current_app, flash, jsonify, redirect, render_template, request,
    session, url_for,
)
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError

from ..extensions import db, limiter
from ..agenda import gerar_ics, link_google, link_outlook
from ..forms import CadastroForm, DenunciaForm, ExcluirContaForm, LembreteForm, LoginForm
from ..models import Acompanhamento, Conteudo, Lembrete, LinkDenunciado, Usuario
from ..models.link_denunciado import CONFIRMADO, PENDENTE
from ..utils import hoje, linhas, url_segura
from ..verificador import dominio_de, eh_oficial

bp = Blueprint("conta", __name__)


# ---------- Quem está logado ----------

def cidadao_atual():
    """Devolve o cidadão logado ou None.

    O db.session.get reaproveita o objeto já carregado na mesma requisição,
    então chamar esta função várias vezes não repete a consulta no banco.
    """
    cidadao_id = session.get("cidadao_id")
    if not cidadao_id:
        return None
    usuario = db.session.get(Usuario, cidadao_id)
    if usuario is None or not usuario.esta_ativo:
        # A conta foi bloqueada ou excluída: quem estava logado sai na hora.
        session.pop("cidadao_id", None)
        return None
    return usuario


def _pedido_por_fetch():
    """O pedido veio do main.js (sem recarregar a página)?"""
    return request.headers.get("X-Requested-With") == "fetch"


def exigir_conta(view):
    """Decorador para as páginas que só funcionam com a pessoa logada."""
    @wraps(view)
    def envolvida(*args, **kwargs):
        if cidadao_atual() is None:
            if _pedido_por_fetch():
                return jsonify(ok=False, mensagem="Entre na sua conta de novo."), 401
            flash("Entre na sua conta para ver esta página.", "aviso")
            return redirect(url_for("conta.entrar"))
        return view(*args, **kwargs)
    return envolvida


@bp.app_context_processor
def disponibilizar_cidadao():
    # Deixa {{ cidadao }} disponível em todos os templates (ex.: ícone do topo).
    return {"cidadao": cidadao_atual()}


@bp.after_request
def sem_cache(resposta):
    # Páginas da conta não ficam guardadas no navegador (computador compartilhado).
    resposta.headers["Cache-Control"] = "no-store"
    return resposta


def _logar(usuario):
    session["cidadao_id"] = usuario.id
    session.permanent = False  # sai ao fechar o navegador


# ---------- Cadastro, entrar e sair ----------

@bp.route("/cadastrar", methods=["GET", "POST"])
@limiter.limit(lambda: current_app.config["LIMITE_LOGIN"], methods=["POST"])
def cadastrar():
    if cidadao_atual():
        return redirect(url_for("conta.minha_area"))
    form = CadastroForm()
    if form.validate_on_submit():
        email = form.email.data.strip().lower()
        if Usuario.query.filter(func.lower(Usuario.email) == email).first():
            form.email.errors.append("Já existe uma conta com esse e-mail. Tente entrar.")
        else:
            usuario = Usuario(email=email, consentimento_em=datetime.now())
            usuario.definir_senha(form.senha.data)
            db.session.add(usuario)
            try:
                db.session.commit()
            except IntegrityError:
                # Dois cadastros com o mesmo e-mail ao mesmo tempo: o UNIQUE do banco segura.
                db.session.rollback()
                form.email.errors.append("Já existe uma conta com esse e-mail. Tente entrar.")
                return render_template("publico/conta/cadastrar.html", form=form)
            # O log não guarda o e-mail (RNF10).
            current_app.logger.info("Conta de cidadão criada (id %s).", usuario.id)
            _logar(usuario)
            flash("Conta criada! Agora você pode salvar temas e criar lembretes.", "sucesso")
            return redirect(url_for("conta.minha_area"))
    return render_template("publico/conta/cadastrar.html", form=form)


@bp.route("/entrar", methods=["GET", "POST"])
# Mesmo limite de tentativas do login do administrador (força bruta).
@limiter.limit(lambda: current_app.config["LIMITE_LOGIN"], methods=["POST"])
def entrar():
    if cidadao_atual():
        return redirect(url_for("conta.minha_area"))
    form = LoginForm()
    if form.validate_on_submit():
        email = form.email.data.strip().lower()
        usuario = Usuario.query.filter(func.lower(Usuario.email) == email).first()
        if usuario and usuario.conferir_senha(form.senha.data):
            if not usuario.esta_ativo:
                # O motivo do bloqueio é interno e não aparece para a pessoa.
                flash("Sua conta está bloqueada. Se achar que é um engano, fale com a "
                      "equipe do guia.", "erro")
                return render_template("publico/conta/entrar.html", form=form)
            _logar(usuario)
            flash("Que bom ver você de novo!", "sucesso")
            return redirect(url_for("conta.minha_area"))
        # Mesma mensagem para e-mail e senha errados, para não revelar qual falhou.
        flash("E-mail ou senha incorretos.", "erro")
    return render_template("publico/conta/entrar.html", form=form)


@bp.route("/sair", methods=["POST"])
def sair():
    # Tira só o cidadão da sessão; se houver admin logado no mesmo navegador, ele continua.
    session.pop("cidadao_id", None)
    flash("Você saiu da sua conta.", "sucesso")
    return redirect(url_for("publico.inicio"))


# ---------- Minha área ----------

@bp.route("/")
@exigir_conta
def minha_area():
    return _mostrar_minha_area(_form_lembrete())


def _mostrar_minha_area(form_lembrete):
    usuario = cidadao_atual()
    return render_template(
        "publico/conta/minha_area.html", usuario=usuario, form_excluir=ExcluirContaForm(),
        form_lembrete=form_lembrete, hoje=hoje(),
        agenda={lembrete.id: _links_da_agenda(lembrete) for lembrete in usuario.lembretes},
    )


@bp.route("/excluir", methods=["POST"])
@exigir_conta
@limiter.limit(lambda: current_app.config["LIMITE_LOGIN"])
def excluir():
    """Exclusão a pedido do titular (LGPD). Pede a senha de novo para confirmar.

    Apaga o e-mail, a senha, os temas salvos e os lembretes. A linha fica,
    sem dados pessoais, para aparecer em "Contas excluídas" no admin.
    """
    usuario = cidadao_atual()
    form = ExcluirContaForm()
    if not (form.validate_on_submit() and usuario.conferir_senha(form.senha.data)):
        flash("Senha incorreta. A conta não foi excluída.", "erro")
        return redirect(url_for("conta.minha_area") + "#excluir")

    usuario_id = usuario.id
    usuario.excluir_conta()
    db.session.commit()
    session.pop("cidadao_id", None)
    current_app.logger.info("Conta de cidadão excluída (id %s).", usuario_id)
    flash("Sua conta e todos os seus dados foram apagados.", "sucesso")
    return redirect(url_for("publico.inicio"))


# ---------- Meu acompanhamento (temas salvos) ----------

def buscar_acompanhamento(usuario, conteudo):
    """Devolve o tema salvo da pessoa, ou None se ela ainda não salvou."""
    return Acompanhamento.query.filter_by(usuario_id=usuario.id, conteudo_id=conteudo.id).first()


def registrar_visita(usuario, conteudo):
    """Abre um tema salvo: devolve o acompanhamento e a data da visita anterior,
    se o conteúdo mudou desde ela (para mostrar o aviso). Sem conta ou tema não salvo: (None, None).
    """
    acompanhamento = buscar_acompanhamento(usuario, conteudo) if usuario else None
    if acompanhamento is None:
        return None, None
    visto_antes = acompanhamento.visto_em if acompanhamento.tem_novidade else None
    acompanhamento.visto_em = datetime.now()
    db.session.commit()
    return acompanhamento, visto_antes


def _salvar_acompanhamento(usuario, conteudo):
    """Salva o tema na conta (se ainda não estiver salvo) e devolve o acompanhamento."""
    acompanhamento = buscar_acompanhamento(usuario, conteudo)
    if acompanhamento is None:
        acompanhamento = Acompanhamento(usuario=usuario, conteudo=conteudo)
        db.session.add(acompanhamento)
        try:
            db.session.flush()
        except IntegrityError:
            # Dois cliques ao mesmo tempo: o UNIQUE do banco segura e usamos o que já existe.
            db.session.rollback()
            acompanhamento = buscar_acompanhamento(usuario, conteudo)
    return acompanhamento


def _numeros_validos(nomes, total):
    """Pega os números marcados no formulário (de 1 até o total) e ignora o resto."""
    numeros = set()
    for valor in request.form.getlist(nomes):
        # isascii(): "²" passa no isdigit(), mas o int() não aceita.
        if valor.isascii() and valor.isdigit() and 1 <= int(valor) <= total:
            numeros.add(int(valor))
    return sorted(numeros)


def _conteudo_publicado(slug):
    return Conteudo.query.filter_by(slug=slug, publicado=True).first_or_404()


def _voltar(conteudo):
    """Volta para a minha área se o pedido veio de lá; senão, para o conteúdo."""
    if request.form.get("origem") == "minha_area":
        return redirect(url_for("conta.minha_area") + "#titulo-temas")
    return redirect(url_for("publico.conteudo", slug=conteudo.slug) + "#acompanhamento")


@bp.route("/temas/<slug>/salvar", methods=["POST"])
@exigir_conta
def salvar_tema(slug):
    conteudo = _conteudo_publicado(slug)
    _salvar_acompanhamento(cidadao_atual(), conteudo)
    db.session.commit()
    flash("Tema salvo! Agora você pode marcar os documentos e os passos.", "sucesso")
    return _voltar(conteudo)


@bp.route("/temas/<slug>/remover", methods=["POST"])
@exigir_conta
def remover_tema(slug):
    # Aqui não exige "publicado": a pessoa pode tirar da lista um tema que saiu do ar.
    conteudo = Conteudo.query.filter_by(slug=slug).first_or_404()
    acompanhamento = buscar_acompanhamento(cidadao_atual(), conteudo)
    if acompanhamento:
        db.session.delete(acompanhamento)
        db.session.commit()
    flash("Tema removido dos seus temas salvos.", "sucesso")
    return _voltar(conteudo)


@bp.route("/temas/<slug>/progresso", methods=["POST"])
@exigir_conta
def salvar_progresso(slug):
    """Guarda os documentos separados e até qual passo a pessoa já fez.

    Marcar qualquer coisa já salva o tema na conta. O main.js manda os dados
    sozinho a cada clique; sem JavaScript, a pessoa usa o botão "Salvar andamento".
    """
    conteudo = _conteudo_publicado(slug)
    acompanhamento = _salvar_acompanhamento(cidadao_atual(), conteudo)

    documentos = _numeros_validos("documentos", len(linhas(conteudo.documentos)))
    passos = _numeros_validos("passos", len(linhas(conteudo.como_solicitar)))
    acompanhamento.documentos_marcados = documentos
    # Marcar o passo 3 quer dizer que o 1 e o 2 também já foram feitos.
    acompanhamento.passo_atual = max(passos, default=0)
    db.session.commit()

    mensagem = "Andamento salvo na sua conta."
    if _pedido_por_fetch():
        return jsonify(ok=True, mensagem=mensagem, passo_atual=acompanhamento.passo_atual)
    flash(mensagem, "sucesso")
    return _voltar(conteudo)


# ---------- Lembretes de prazo ----------

def _form_lembrete():
    """Formulário de lembrete com a lista de temas publicados para escolher."""
    form = LembreteForm()
    temas = Conteudo.query.filter_by(publicado=True).order_by(Conteudo.titulo).all()
    form.conteudo_id.choices = [(0, "Nenhum tema")] + [(c.id, c.titulo) for c in temas]
    return form


def _link_do_tema(lembrete):
    conteudo = lembrete.conteudo
    if conteudo is None or not conteudo.publicado:
        return None
    return url_for("publico.conteudo", slug=conteudo.slug, _external=True)


def _links_da_agenda(lembrete):
    link = _link_do_tema(lembrete)
    return {
        "google": link_google(lembrete.titulo, lembrete.data, link),
        "outlook": link_outlook(lembrete.titulo, lembrete.data, link),
        "ics": url_for("conta.baixar_lembrete", lembrete_id=lembrete.id),
    }


def _lembrete_da_pessoa(lembrete_id):
    """Só o dono enxerga o lembrete; para os outros é como se não existisse (404)."""
    return Lembrete.query.filter_by(
        id=lembrete_id, usuario_id=cidadao_atual().id
    ).first_or_404()


@bp.route("/lembretes", methods=["POST"])
@exigir_conta
def criar_lembrete():
    usuario = cidadao_atual()
    form = _form_lembrete()
    veio_do_tema = request.form.get("origem") == "conteudo"
    conteudo = db.session.get(Conteudo, form.conteudo_id.data) if form.conteudo_id.data else None

    if not form.validate_on_submit():
        if veio_do_tema and conteudo:
            # Na página do tema o formulário é pequeno: mostra o erro como aviso.
            for erros in form.errors.values():
                for erro in erros:
                    flash(erro, "erro")
            return redirect(url_for("publico.conteudo", slug=conteudo.slug) + "#acompanhamento")
        return _mostrar_minha_area(form)

    if conteudo:
        # Criar um lembrete para um tema também salva o tema na conta. Vem antes do
        # lembrete porque, num clique duplo, o rollback descartaria o lembrete junto.
        _salvar_acompanhamento(usuario, conteudo)
    lembrete = Lembrete(usuario=usuario, conteudo=conteudo, titulo=form.titulo.data,
                        data=form.prazo.data)
    db.session.add(lembrete)
    db.session.commit()
    flash("Lembrete criado! Agora escolha a sua agenda para receber o aviso.", "sucesso")
    return redirect(url_for("conta.minha_area") + f"#lembrete-{lembrete.id}")


@bp.route("/lembretes/<int:lembrete_id>/excluir", methods=["POST"])
@exigir_conta
def excluir_lembrete(lembrete_id):
    db.session.delete(_lembrete_da_pessoa(lembrete_id))
    db.session.commit()
    flash("Lembrete excluído.", "sucesso")
    return redirect(url_for("conta.minha_area") + "#titulo-lembretes")


@bp.route("/lembretes/<int:lembrete_id>.ics")
@exigir_conta
def baixar_lembrete(lembrete_id):
    """Arquivo de agenda (.ics) para iPhone, Mac e o app Calendário do Windows."""
    lembrete = _lembrete_da_pessoa(lembrete_id)
    texto = gerar_ics(
        uid=f"lembrete-{lembrete.id}@guia-do-cidadao-perdido",
        titulo=lembrete.titulo, data=lembrete.data, link_do_tema=_link_do_tema(lembrete),
    )
    # "inline": no iPhone o Safari já abre a tela "Adicionar ao Calendário";
    # no computador o navegador baixa o arquivo, que abre com dois cliques.
    return Response(texto, mimetype="text/calendar", headers={
        "Content-Disposition": f'inline; filename="lembrete-{lembrete.id}.ics"',
    })


# ---------- Denúncia de link suspeito (só com conta) ----------

@bp.route("/denuncias", methods=["POST"])
@exigir_conta
@limiter.limit(lambda: current_app.config["LIMITE_DENUNCIA"])
def denunciar_link():
    """O cidadão denuncia um link; o admin revisa antes de ele entrar no verificador."""
    voltar = redirect(url_for("publico.verificar_golpe") + "#denunciar")
    form = DenunciaForm()
    if not form.validate_on_submit():
        flash(next(iter(form.errors.values()))[0], "erro")
        return voltar

    url = form.url.data
    if "://" not in url:
        url = "https://" + url  # links de SMS costumam vir sem o https://
    dominio = dominio_de(url)
    if not url_segura(url) or not dominio or "." not in dominio:
        flash("Isso não parece um link. Cole o endereço completo, ex.: site-estranho.com/pagar.", "erro")
        return voltar
    if eh_oficial(dominio):
        flash(f"{dominio} é um endereço oficial do governo, então não entra como denúncia. "
              "Se a mensagem pedia senha ou pagamento, desconfie mesmo assim.", "aviso")
        return voltar

    if LinkDenunciado.query.filter_by(dominio=dominio, status=CONFIRMADO).first():
        flash(f"{dominio} já está confirmado como golpe. Obrigado por avisar!", "sucesso")
        return voltar
    # O mesmo link já esperando revisão (de qualquer pessoa) não entra de novo.
    repetida = LinkDenunciado.query.filter_by(url=url, status=PENDENTE).first()
    if not repetida:
        db.session.add(LinkDenunciado(usuario=cidadao_atual(), url=url, dominio=dominio,
                                      descricao=form.descricao.data or None))
        db.session.commit()
        current_app.logger.info("Nova denúncia de link (domínio %s).", dominio)
    flash("Obrigado! A equipe do guia vai revisar o link. Se for golpe, o verificador passa a "
          "avisar todo mundo.", "sucesso")
    return voltar
