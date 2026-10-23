"""Testes das tabelas dos diferenciais (migração 0002): conta do cidadão,
acompanhamento, lembretes, denúncia de links e glossário."""
from datetime import date, datetime, timedelta

import pytest
from sqlalchemy.exc import IntegrityError

from app.extensions import db
from app.models import (Acompanhamento, Conteudo, Lembrete, LinkDenunciado,
                        TermoGlossario, Usuario)


def _usuario(email="cidadao@exemplo.com.br"):
    usuario = Usuario(email=email, consentimento_em=datetime.now())
    usuario.definir_senha("senha-do-cidadao")
    db.session.add(usuario)
    db.session.commit()
    return usuario


def _cnh():
    return Conteudo.query.filter_by(slug="primeira-habilitacao-cnh").one()


def test_senha_do_cidadao_fica_em_hash(app):
    usuario = _usuario()
    assert usuario.senha_hash != "senha-do-cidadao"
    assert usuario.conferir_senha("senha-do-cidadao")
    assert not usuario.conferir_senha("errada")


def test_email_do_cidadao_e_unico(app):
    _usuario()
    with pytest.raises(IntegrityError):
        _usuario()
    db.session.rollback()


def test_excluir_conta_apaga_temas_e_lembretes_mas_mantem_denuncia(app):
    usuario = _usuario()
    cnh = _cnh()
    db.session.add_all([
        Acompanhamento(usuario=usuario, conteudo=cnh, passo_atual=1, documentos_marcados=[1]),
        Lembrete(usuario=usuario, conteudo=cnh, titulo="Prova teórica", data=date(2026, 12, 1)),
        LinkDenunciado(usuario=usuario, url="http://cnh-facil.com/pix", dominio="cnh-facil.com"),
    ])
    db.session.commit()

    db.session.delete(usuario)
    db.session.commit()

    assert Acompanhamento.query.count() == 0
    assert Lembrete.query.count() == 0
    denuncia = LinkDenunciado.query.one()
    assert denuncia.usuario_id is None
    assert denuncia.status == "pendente"


def test_mesmo_tema_nao_e_salvo_duas_vezes(app):
    usuario = _usuario()
    cnh = _cnh()
    db.session.add(Acompanhamento(usuario=usuario, conteudo=cnh))
    db.session.commit()
    db.session.add(Acompanhamento(usuario=usuario, conteudo=cnh))
    with pytest.raises(IntegrityError):
        db.session.commit()
    db.session.rollback()


def test_checklist_salvo_na_conta_volta_igual(app):
    usuario = _usuario()
    db.session.add(Acompanhamento(usuario=usuario, conteudo=_cnh(), documentos_marcados=[1, 3]))
    db.session.commit()
    db.session.expire_all()
    assert Acompanhamento.query.one().documentos_marcados == [1, 3]


def test_aviso_quando_o_conteudo_muda_depois_da_visita(app):
    usuario = _usuario()
    cnh = _cnh()
    acompanhamento = Acompanhamento(usuario=usuario, conteudo=cnh, visto_em=datetime.now())
    db.session.add(acompanhamento)
    db.session.commit()
    assert not acompanhamento.tem_novidade

    cnh.atualizado_em = acompanhamento.visto_em + timedelta(minutes=5)
    db.session.commit()
    assert acompanhamento.tem_novidade


def test_excluir_conteudo_deixa_lembrete_sem_tema(app):
    usuario = _usuario()
    cnh = _cnh()
    db.session.add(Lembrete(usuario=usuario, conteudo=cnh, titulo="Exame médico",
                            data=date(2026, 11, 20)))
    db.session.commit()

    db.session.delete(cnh)
    db.session.commit()

    lembrete = Lembrete.query.one()
    assert lembrete.conteudo_id is None
    assert lembrete.titulo == "Exame médico"


def test_status_da_denuncia_so_aceita_os_tres_valores(app):
    db.session.add(LinkDenunciado(url="http://x.com", dominio="x.com", status="qualquer"))
    with pytest.raises(IntegrityError):
        db.session.commit()
    db.session.rollback()


def test_termos_iniciais_do_glossario_sao_validos():
    from app.dados_iniciais import GLOSSARIO

    termos = [t["termo"] for t in GLOSSARIO]
    assert len(termos) == len(set(termos))
    assert all(len(t["termo"]) <= 80 and len(t["explicacao"]) <= 400 for t in GLOSSARIO)


def test_comando_dados_iniciais_cadastra_o_glossario_sem_repetir(app):
    rodar = app.test_cli_runner()
    rodar.invoke(args=["dados-iniciais"])
    total = TermoGlossario.query.count()
    assert total > 0
    rodar.invoke(args=["dados-iniciais"])  # rodar de novo não duplica
    assert TermoGlossario.query.count() == total
