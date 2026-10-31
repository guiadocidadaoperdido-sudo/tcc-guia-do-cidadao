"""Glossário "O que é isso?": sublinha os termos difíceis nos textos do guia.

No template: {{ p | glossario("o_que_e") }}. O nome da parte serve para
sublinhar cada termo só na primeira vez em que ele aparece naquela parte
(ex.: "CPF" uma vez em "O que é" e uma vez em "Quem tem direito").

Cada termo vira um link para /glossario#slug. O main.js transforma o link num
balão com a explicação; sem JavaScript, o link leva para a página do glossário.
"""
import re

from flask import g, url_for
from markupsafe import Markup, escape

from .extensions import db
from .models import TermoGlossario
from .utils import gerar_slug


def _termos():
    """Carrega os termos uma vez por página (fica guardado no g da requisição)."""
    if "glossario" not in g:
        termos = db.session.execute(db.select(TermoGlossario)).scalars().all()
        por_nome = {t.termo.lower(): t for t in termos}
        # Os termos maiores primeiro: "Cadastro Único" ganha de um possível "Cadastro".
        nomes = sorted(por_nome, key=len, reverse=True)
        # O texto é escapado antes de procurar, então o termo também é escapado.
        # (?<!\w) e (?!\w): só a palavra inteira ("CPF" não marca dentro de "CPFs").
        padrao = (re.compile(
            r"(?<!\w)(" + "|".join(re.escape(str(escape(n))) for n in nomes) + r")(?!\w)",
            re.IGNORECASE,
        ) if nomes else None)
        g.glossario = {"padrao": padrao, "por_nome": por_nome, "usados": {}}
    return g.glossario


def marcar_termos(texto, parte):
    """Devolve o texto (já escapado) com os termos do glossário marcados."""
    seguro = str(escape(texto or ""))
    dados = _termos()
    if dados["padrao"] is None:
        return Markup(seguro)
    usados = dados["usados"].setdefault(parte, set())

    def trocar(achado):
        palavra = achado.group(1)
        termo = dados["por_nome"].get(Markup(palavra).unescape().lower())
        if termo is None or termo.id in usados:
            return palavra
        usados.add(termo.id)
        link = url_for("publico.glossario") + "#" + gerar_slug(termo.termo)
        return (f'<a class="termo" href="{escape(link)}" '
                f'data-explicacao="{escape(termo.explicacao)}">{palavra}</a>')

    return Markup(dados["padrao"].sub(trocar, seguro))
