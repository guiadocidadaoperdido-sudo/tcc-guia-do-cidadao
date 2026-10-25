"""Funções auxiliares usadas nas rotas e nos templates."""
import re
import unicodedata
from datetime import datetime
from zoneinfo import ZoneInfo

# O servidor do Render fica em UTC; as datas do site seguem o horário de Brasília.
FUSO_BRASIL = ZoneInfo("America/Sao_Paulo")

MESES = [
    "janeiro", "fevereiro", "março", "abril", "maio", "junho",
    "julho", "agosto", "setembro", "outubro", "novembro", "dezembro",
]


def gerar_slug(texto):
    """Transforma 'Minha Casa, Minha Vida' em 'minha-casa-minha-vida'."""
    sem_acento = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode("ascii")
    slug = re.sub(r"[^a-z0-9]+", "-", sem_acento.lower()).strip("-")
    return slug[:150]


def hoje():
    """Data de hoje no Brasil. Às 22h em São Paulo o servidor (UTC) já está no dia seguinte."""
    return datetime.now(FUSO_BRASIL).date()


def formatar_data(data):
    """Mostra a data por extenso: 16 de outubro de 2026."""
    if not data:
        return ""
    return f"{data.day} de {MESES[data.month - 1]} de {data.year}"


def paragrafos(texto):
    """Divide o texto em parágrafos separados por linha em branco."""
    if not texto:
        return []
    return [p.strip() for p in re.split(r"\n\s*\n", texto.strip()) if p.strip()]


def linhas(texto):
    """Divide o texto em itens, um por linha (usado em listas e passo a passo)."""
    if not texto:
        return []
    itens = []
    for linha in texto.splitlines():
        linha = re.sub(r"^\s*(?:[-*•]|\d+[.)])\s*", "", linha).strip()
        if linha:
            itens.append(linha)
    return itens


def url_segura(url):
    """Aceita apenas endereços http ou https para as fontes oficiais."""
    return bool(re.match(r"^https?://[^\s/$.?#][^\s]*$", url or "", re.IGNORECASE))
