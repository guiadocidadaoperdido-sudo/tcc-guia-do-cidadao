"""Models: classes ligadas às tabelas do banco.

As cinco primeiras são as da seção 3.5 do TCC. As outras cinco são dos
diferenciais: conta do cidadão, acompanhamento, lembretes, denúncia de links
e glossário.
"""
from .acompanhamento import Acompanhamento
from .administrador import Administrador
from .avaliacao import Avaliacao
from .categoria import Categoria
from .conteudo import Conteudo
from .fonte_oficial import FonteOficial
from .lembrete import Lembrete
from .link_denunciado import LinkDenunciado
from .termo_glossario import TermoGlossario
from .usuario import Usuario

__all__ = [
    "Acompanhamento", "Administrador", "Avaliacao", "Categoria", "Conteudo",
    "FonteOficial", "Lembrete", "LinkDenunciado", "TermoGlossario", "Usuario",
]
