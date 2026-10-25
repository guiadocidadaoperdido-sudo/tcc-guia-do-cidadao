"""Verificador de golpe: confere um link ou uma mensagem inteira (SMS, WhatsApp, e-mail).

Não usa inteligência artificial nem serviço de fora: são regras simples, que
dá para explicar uma por uma. Ele NÃO garante que algo é seguro; só aponta os
sinais mais comuns dos golpes que usam o nome do governo.

Três resultados:
- ALTO: "Muito suspeito" (link denunciado, endereço que imita o governo,
  pedido de senha ou código, pagamento junto com link que não é oficial).
- ATENCAO: "Tenha cuidado" (algum sinal de alerta, mas nada decisivo).
- SEM_SINAIS: "Não achamos sinais de golpe" (o que não quer dizer que é seguro).

Função pura (sem banco e sem Flask): a lista de domínios denunciados chega
como parâmetro.
"""
import ipaddress
import re
import unicodedata
from dataclasses import dataclass, field
from urllib.parse import urlsplit

ALTO = "alto"
ATENCAO = "atencao"
SEM_SINAIS = "sem_sinais"

# Terminações de sites oficiais no Brasil: governo, Forças Armadas, Justiça,
# Legislativo e Ministério Público. Ex.: www.gov.br, alistamento.eb.mil.br.
DOMINIOS_OFICIAIS = ("gov.br", "mil.br", "jus.br", "leg.br", "mp.br")

# Encurtadores escondem o endereço de verdade.
ENCURTADORES = {
    "bit.ly", "tinyurl.com", "cutt.ly", "is.gd", "t.co", "goo.gl", "ow.ly",
    "encurtador.com.br", "abre.ai", "rebrand.ly", "shorturl.at", "s.id",
}

# Palavras que os golpistas colocam no endereço para parecer do governo.
NOMES_DO_GOVERNO = (
    "gov", "govbr", "receita", "inss", "detran", "caixa", "bolsafamilia", "bolsa-familia",
    "cnh", "serasa", "correios", "poupatempo", "meuinss", "fgts", "pis", "cadunico",
)

# Links: com http(s)://, começando com www. ou só "algo.com/...".
PADRAO_LINK = re.compile(
    r"(?:https?://|www\.)[^\s<>\"']+"
    r"|\b(?:[a-z0-9-]+\.)+(?:com|net|org|br|info|xyz|top|site|online|io|me|ly|app|link|click|shop|vip)"
    r"(?:/[^\s<>\"']*)?",
    re.IGNORECASE,
)

# Sinais no texto da mensagem (comparados sem acento e em minúsculas).
SINAIS_TEXTO = {
    "senha": (r"\bsenha\b|\bcodigo\b|\btoken\b|codigo de (verificacao|seguranca)|\bpin\b",
              "Pede senha ou código. Órgão público nunca pede senha ou código por mensagem."),
    "pagamento": (r"\bpix\b|chave pix|\btaxa\b|\bboleto\b|\bpague\b|\bpagar\b|pagamento|deposito|tarifa",
                  "Fala em pagamento (Pix, taxa ou boleto). Os serviços do gov.br costumam ser "
                  "gratuitos, e cobrança de verdade aparece no app ou site oficial."),
    "urgencia": (r"urgente|imediatamente|ultimo dia|ultimas horas|\bhoje\b|24 ?h|prazo final"
                 r"|sera (bloquead|cancelad|suspens)|(bloquead|cancelad|suspens)[oa]",
                 "Tenta apressar você (urgente, último dia, conta bloqueada). Pressa é a "
                 "principal arma do golpe."),
    "premio": (r"premio|sorteio|voce ganhou|valor a receber|dinheiro esquecido|restituicao"
               r"|beneficio liberado|saque liberado|indenizacao",
               "Promete dinheiro ou benefício liberado. Confira sempre no site ou app oficial."),
    "dados": (r"\bcpf\b|dados bancarios|numero do cartao|cartao de credito|atualize (seu|os) cadastro",
              "Pede dados pessoais ou do banco (CPF, cartão, cadastro)."),
}


@dataclass
class Link:
    url: str
    dominio: str
    oficial: bool


@dataclass
class Resultado:
    nivel: str = SEM_SINAIS
    motivos: list = field(default_factory=list)
    links: list = field(default_factory=list)

    def alerta(self, nivel, motivo):
        """Guarda o motivo e sobe o nível (nunca desce: ALTO ganha de ATENCAO)."""
        if motivo not in self.motivos:
            self.motivos.append(motivo)
        if nivel == ALTO or self.nivel == SEM_SINAIS:
            self.nivel = nivel


def _sem_acento(texto):
    texto = unicodedata.normalize("NFKD", texto)
    return "".join(c for c in texto if not unicodedata.combining(c)).lower()


def dominio_de(url):
    """Pega só o domínio: "https://www.Gov.br/inss?x=1" vira "www.gov.br"."""
    url = url.strip()
    if not re.match(r"^[a-z][a-z0-9+.-]*://", url, re.IGNORECASE):
        url = "http://" + url
    dominio = (urlsplit(url).hostname or "").lower().rstrip(".")
    return dominio


def eh_oficial(dominio):
    return any(dominio == d or dominio.endswith("." + d) for d in DOMINIOS_OFICIAIS)


def _sem_www(dominio):
    return dominio[4:] if dominio.startswith("www.") else dominio


def achar_links(texto):
    """Lista os links do texto, sem repetir, com o domínio de cada um."""
    links, vistos = [], set()
    for trecho in PADRAO_LINK.findall(texto or ""):
        url = trecho.rstrip(".,;:!?)]}")
        dominio = dominio_de(url)
        if dominio and url.lower() not in vistos:
            vistos.add(url.lower())
            links.append(Link(url=url, dominio=dominio, oficial=eh_oficial(dominio)))
    return links


def _conferir_link(link, resultado, denunciados):
    dominio = link.dominio
    if _sem_www(dominio) in denunciados:
        resultado.alerta(ALTO, f"O endereço {dominio} já foi denunciado e confirmado como golpe "
                               "pela equipe do guia.")
    if link.oficial:
        return
    try:
        ipaddress.ip_address(dominio)
        resultado.alerta(ALTO, f"O link usa um número ({dominio}) no lugar do nome do site. "
                               "Sites oficiais não fazem isso.")
        return
    except ValueError:
        pass
    if dominio.startswith("xn--") or ".xn--" in dominio:
        resultado.alerta(ALTO, f"O endereço {dominio} usa letras disfarçadas para imitar outro site.")
    if _sem_www(dominio) in ENCURTADORES:
        resultado.alerta(ATENCAO, f"O link {dominio} é encurtado e esconde o endereço de verdade.")
        return
    # Nomes curtos (gov, cnh, pis) só contam como pedaço inteiro do endereço,
    # para "pisos.com" não virar golpe; os longos (receita, detran) valem em qualquer lugar.
    partes = re.split(r"[.-]", dominio)
    if any(nome in partes if len(nome) <= 4 else nome in dominio for nome in NOMES_DO_GOVERNO):
        resultado.alerta(ALTO, f"O endereço {dominio} imita um órgão do governo, mas não "
                               "termina em .gov.br.")
    else:
        resultado.alerta(ATENCAO, f"O endereço {dominio} não é de um site oficial do governo "
                                  "(.gov.br).")
    if link.url.lower().startswith("http://"):
        resultado.alerta(ATENCAO, f"O link {dominio} não usa conexão segura (https).")


def verificar(texto, denunciados=()):
    """Confere o texto colado e devolve um Resultado com o nível e os motivos.

    denunciados: domínios confirmados como golpe pelo admin (sem "www.").
    """
    resultado = Resultado()
    texto = (texto or "")[:5000]
    denunciados = {_sem_www(d.lower()) for d in denunciados}

    resultado.links = achar_links(texto)
    for link in resultado.links:
        _conferir_link(link, resultado, denunciados)

    normal = _sem_acento(texto)
    achados = {nome for nome, (padrao, _) in SINAIS_TEXTO.items() if re.search(padrao, normal)}
    tem_link_estranho = any(not link.oficial for link in resultado.links)
    for nome in SINAIS_TEXTO:
        if nome not in achados:
            continue
        motivo = SINAIS_TEXTO[nome][1]
        # Pedir senha é golpe sempre; pedir pagamento junto com link que não é
        # oficial também. O resto é sinal de atenção.
        decisivo = nome == "senha" or (nome == "pagamento" and tem_link_estranho)
        resultado.alerta(ALTO if decisivo else ATENCAO, motivo)
    return resultado
