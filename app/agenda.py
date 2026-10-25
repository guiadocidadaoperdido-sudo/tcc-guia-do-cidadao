"""Leva um lembrete para a agenda da pessoa: Google Agenda, Outlook e arquivo .ics.

O lembrete é um evento de dia inteiro. O arquivo .ics é o formato padrão de
agenda (RFC 5545): abre no app Calendário do iPhone, do Mac, do Windows e
também no Google e no Outlook. Só ele aceita alarme; os links do Google e do
Outlook usam o aviso padrão da agenda da pessoa.

Funções puras (sem banco e sem Flask) para ficarem fáceis de testar.
"""
from datetime import datetime, timedelta, timezone
from urllib.parse import urlencode

GOOGLE = "https://calendar.google.com/calendar/render"
OUTLOOK = "https://outlook.live.com/calendar/0/deeplink/compose"


def _descricao(link_do_tema):
    texto = "Lembrete criado no Guia do Cidadão Perdido."
    if link_do_tema:
        texto += f" Veja o passo a passo: {link_do_tema}"
    return texto


def link_google(titulo, data, link_do_tema=None):
    # Dia inteiro no Google: a data final é o dia seguinte (não incluído).
    dias = f"{data:%Y%m%d}/{data + timedelta(days=1):%Y%m%d}"
    return GOOGLE + "?" + urlencode({
        "action": "TEMPLATE", "text": titulo, "dates": dias,
        "details": _descricao(link_do_tema),
    })


def link_outlook(titulo, data, link_do_tema=None):
    return OUTLOOK + "?" + urlencode({
        "path": "/calendar/action/compose", "rru": "addevent", "subject": titulo,
        "startdt": data.isoformat(), "enddt": (data + timedelta(days=1)).isoformat(),
        "allday": "true", "body": _descricao(link_do_tema),
    })


def _escapar(texto):
    """No .ics, barra invertida, vírgula, ponto e vírgula e quebra de linha precisam de escape."""
    return (
        texto.replace("\\", "\\\\").replace(";", "\\;").replace(",", "\\,")
        .replace("\r\n", "\\n").replace("\r", "\\n").replace("\n", "\\n")
    )


def _dobrar(linha):
    """O padrão pede linhas de no máximo 75 bytes; o resto continua na linha de baixo com um espaço."""
    partes, atual = [], ""
    for letra in linha:
        if len((atual + letra).encode("utf-8")) > 75:
            partes.append(atual)
            atual = " " + letra
        else:
            atual += letra
    partes.append(atual)
    return "\r\n".join(partes)


def gerar_ics(uid, titulo, data, link_do_tema=None, agora=None):
    """Monta o texto do arquivo .ics de um evento de dia inteiro, com alarme 1 dia antes."""
    agora = agora or datetime.now(timezone.utc)
    linhas = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//Guia do Cidadao Perdido//Lembretes//PT-BR",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
        "BEGIN:VEVENT",
        f"UID:{uid}",
        f"DTSTAMP:{agora:%Y%m%dT%H%M%SZ}",
        f"DTSTART;VALUE=DATE:{data:%Y%m%d}",
        f"DTEND;VALUE=DATE:{data + timedelta(days=1):%Y%m%d}",
        f"SUMMARY:{_escapar(titulo)}",
        f"DESCRIPTION:{_escapar(_descricao(link_do_tema))}",
    ]
    if link_do_tema:
        linhas.append(f"URL:{link_do_tema}")
    linhas += [
        "BEGIN:VALARM",
        "ACTION:DISPLAY",
        f"DESCRIPTION:{_escapar(titulo)}",
        # Num evento de dia inteiro, 1 dia antes = véspera à 0h. Muitas agendas
        # mostram o aviso logo de manhã.
        "TRIGGER:-P1D",
        "END:VALARM",
        "END:VEVENT",
        "END:VCALENDAR",
    ]
    return "\r\n".join(_dobrar(linha) for linha in linhas) + "\r\n"
