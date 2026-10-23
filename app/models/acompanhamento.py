from datetime import datetime

from ..extensions import db


class Acompanhamento(db.Model):
    """Tema salvo por um cidadão, com o andamento dele no processo.

    - passo_atual: quantos passos do "Como solicitar" a pessoa já fez.
    - documentos_marcados: números (começando em 1) dos documentos que ela já
      separou no checklist.
    - visto_em: última vez que ela abriu o tema. Se o conteúdo foi atualizado
      depois disso, o site mostra um aviso.
    """
    __tablename__ = "acompanhamento"
    __table_args__ = (
        db.UniqueConstraint("usuario_id", "conteudo_id", name="uq_acompanhamento_usuario_conteudo"),
    )

    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(
        db.Integer, db.ForeignKey("usuario.id", ondelete="CASCADE"), nullable=False
    )
    conteudo_id = db.Column(
        db.Integer, db.ForeignKey("conteudo.id", ondelete="CASCADE"), nullable=False
    )
    passo_atual = db.Column(db.Integer, nullable=False, default=0)
    documentos_marcados = db.Column(db.JSON, nullable=False, default=list)
    visto_em = db.Column(db.DateTime, nullable=False, default=datetime.now)
    criado_em = db.Column(db.DateTime, nullable=False, default=datetime.now)

    usuario = db.relationship("Usuario", back_populates="acompanhamentos")
    conteudo = db.relationship("Conteudo", back_populates="acompanhamentos")

    @property
    def tem_novidade(self):
        """O conteúdo mudou depois da última visita da pessoa?"""
        return self.conteudo.atualizado_em > self.visto_em
