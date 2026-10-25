"""Testes dos lembretes de prazo e dos links para a agenda (Google, Outlook e .ics)."""
from datetime import date, datetime, timedelta, timezone
from urllib.parse import parse_qs, urlparse

from app.agenda import gerar_ics, link_google, link_outlook
from app import utils
from app.extensions import db
from app.models import Acompanhamento, Conteudo, Lembrete
from app.utils import hoje

from conftest import _cadastrar

DATA = date(2027, 6, 30)
AMANHA = hoje() + timedelta(days=1)


def _cnh():
    return Conteudo.query.filter_by(slug="primeira-habilitacao-cnh").one()


def _criar(cliente, titulo="Prova teórica", data=AMANHA, conteudo_id=0, **extra):
    dados = {"titulo": titulo, "prazo": data.isoformat() if data else "",
             "conteudo_id": str(conteudo_id), **extra}
    return cliente.post("/conta/lembretes", data=dados)


# ---------- Funções da agenda (sem banco) ----------

def test_link_do_google_e_dia_inteiro():
    url = urlparse(link_google("Prova teórica", DATA, "https://site/conteudo/cnh"))
    dados = parse_qs(url.query)
    assert url.netloc == "calendar.google.com"
    assert dados["action"] == ["TEMPLATE"]
    assert dados["text"] == ["Prova teórica"]
    assert dados["dates"] == ["20270630/20270701"]
    assert "https://site/conteudo/cnh" in dados["details"][0]


def test_link_do_outlook():
    dados = parse_qs(urlparse(link_outlook("Prova", DATA)).query)
    assert dados["startdt"] == ["2027-06-30"]
    assert dados["enddt"] == ["2027-07-01"]
    assert dados["allday"] == ["true"]


def test_ics_com_alarme_um_dia_antes():
    agora = datetime(2026, 10, 25, 12, 0, tzinfo=timezone.utc)
    texto = gerar_ics("lembrete-1@guia", "Exame, médico; levar RG", DATA, agora=agora)
    linhas = texto.split("\r\n")
    assert linhas[0] == "BEGIN:VCALENDAR" and texto.endswith("END:VCALENDAR\r\n")
    assert "DTSTART;VALUE=DATE:20270630" in linhas
    assert "DTEND;VALUE=DATE:20270701" in linhas
    assert "DTSTAMP:20261025T120000Z" in linhas
    assert r"SUMMARY:Exame\, médico\; levar RG" in linhas
    assert "TRIGGER:-P1D" in linhas


def test_ics_quebra_linhas_compridas_sem_estragar_acentos():
    titulo = "Exame médico e prova de direção " * 6
    texto = gerar_ics("x", titulo.strip(), DATA)
    for linha in texto.split("\r\n"):
        assert len(linha.encode("utf-8")) <= 75
    # Juntando as linhas de volta (o padrão tira o CRLF + espaço), o título volta igual.
    assert f"SUMMARY:{titulo.strip()}" in texto.replace("\r\n ", "")


def test_ics_nao_deixa_quebra_de_linha_no_titulo():
    texto = gerar_ics("x", "Prova\rBEGIN:VEVENT", DATA)
    assert "SUMMARY:Prova\\nBEGIN:VEVENT" in texto
    # Só existe um evento de verdade: nenhuma linha nova começa com BEGIN:VEVENT por causa do título.
    assert texto.split("\r\n").count("BEGIN:VEVENT") == 1


def test_hoje_segue_o_horario_de_brasilia(monkeypatch):
    # 26/10 às 01h em UTC ainda é 25/10 às 22h em São Paulo.
    class RelogioFalso(datetime):
        @classmethod
        def now(cls, tz=None):
            return datetime(2026, 10, 26, 1, 0, tzinfo=timezone.utc).astimezone(tz)
    monkeypatch.setattr(utils, "datetime", RelogioFalso)
    assert utils.hoje() == date(2026, 10, 25)


# ---------- Criar, baixar e excluir ----------

def test_lembrete_exige_conta(cliente):
    assert _criar(cliente).headers["Location"].endswith("/conta/entrar")
    assert cliente.get("/conta/lembretes/1.ics").headers["Location"].endswith("/conta/entrar")


def test_criar_lembrete_na_minha_area(cidadao_logado):
    resposta = _criar(cidadao_logado)
    lembrete = Lembrete.query.one()
    assert resposta.headers["Location"].endswith(f"/conta/#lembrete-{lembrete.id}")
    assert lembrete.conteudo is None

    html = cidadao_logado.get("/conta/").get_data(as_text=True)
    assert "Prova teórica" in html
    assert "calendar.google.com" in html
    assert "outlook.live.com" in html
    assert f"/conta/lembretes/{lembrete.id}.ics" in html


def test_lembrete_nao_aceita_data_no_passado(cidadao_logado):
    html = _criar(cidadao_logado, data=hoje() - timedelta(days=1)).get_data(as_text=True)
    assert "Escolha hoje ou uma data futura" in html
    html = _criar(cidadao_logado, data=None).get_data(as_text=True)
    assert "Escolha uma data válida" in html
    assert Lembrete.query.count() == 0


def test_lembrete_nao_aceita_tema_em_rascunho(cidadao_logado):
    rascunho = Conteudo.query.filter_by(slug="minha-casa-minha-vida").one()
    _criar(cidadao_logado, conteudo_id=rascunho.id)
    assert Lembrete.query.count() == 0


def test_lembrete_criado_no_tema_salva_o_tema(cidadao_logado):
    cnh = _cnh()
    html = cidadao_logado.get(f"/conteudo/{cnh.slug}").get_data(as_text=True)
    assert "Criar lembrete de prazo" in html

    _criar(cidadao_logado, conteudo_id=cnh.id, origem="conteudo")
    assert Lembrete.query.one().conteudo == cnh
    assert Acompanhamento.query.count() == 1


def test_erro_no_lembrete_do_tema_volta_para_o_tema(cidadao_logado):
    cnh = _cnh()
    resposta = _criar(cidadao_logado, conteudo_id=cnh.id, origem="conteudo",
                      data=hoje() - timedelta(days=3))
    assert resposta.headers["Location"].endswith(f"/conteudo/{cnh.slug}#acompanhamento")
    assert "Escolha hoje ou uma data futura" in cidadao_logado.get(
        resposta.headers["Location"]).get_data(as_text=True)


def test_baixar_ics(cidadao_logado):
    _criar(cidadao_logado, titulo="Exame médico", conteudo_id=_cnh().id)
    lembrete = Lembrete.query.one()
    resposta = cidadao_logado.get(f"/conta/lembretes/{lembrete.id}.ics")
    assert resposta.mimetype == "text/calendar"
    texto = resposta.get_data(as_text=True)
    assert "SUMMARY:Exame médico" in texto
    assert "/conteudo/primeira-habilitacao-cnh" in texto
    assert resposta.headers["Cache-Control"] == "no-store"


def test_lembrete_de_outra_pessoa_da_404(cliente):
    _cadastrar(cliente)
    _criar(cliente)
    lembrete_id = Lembrete.query.one().id
    cliente.post("/conta/sair")

    _cadastrar(cliente, email="joao@exemplo.com.br")
    assert cliente.get(f"/conta/lembretes/{lembrete_id}.ics").status_code == 404
    assert cliente.post(f"/conta/lembretes/{lembrete_id}/excluir").status_code == 404
    assert Lembrete.query.count() == 1


def test_excluir_lembrete(cidadao_logado):
    _criar(cidadao_logado)
    cidadao_logado.post(f"/conta/lembretes/{Lembrete.query.one().id}/excluir")
    assert Lembrete.query.count() == 0


def test_lembrete_vencido_aparece_como_ja_passou(cidadao_logado):
    _criar(cidadao_logado)
    Lembrete.query.one().data = hoje() - timedelta(days=2)
    db.session.commit()
    html = cidadao_logado.get("/conta/").get_data(as_text=True)
    assert "Já passou" in html
    assert "calendar.google.com" not in html
