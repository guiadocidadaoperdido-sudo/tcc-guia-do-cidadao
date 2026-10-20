"""Models: classes ligadas às cinco tabelas do banco (seção 3.5 do TCC)."""
from .administrador import Administrador
from .avaliacao import Avaliacao
from .categoria import Categoria
from .conteudo import Conteudo
from .fonte_oficial import FonteOficial

__all__ = ["Administrador", "Avaliacao", "Categoria", "Conteudo", "FonteOficial"]
