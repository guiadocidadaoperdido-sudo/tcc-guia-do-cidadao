from datetime import datetime

from flask import current_app
from itsdangerous import BadSignature, URLSafeTimedSerializer
from werkzeug.security import check_password_hash, generate_password_hash

from ..extensions import db

# Situação da conta. São as três telas do admin: ativas, bloqueadas e excluídas.
ATIVO = "ativo"
BLOQUEADO = "bloqueado"
EXCLUIDO = "excluido"


class Usuario(db.Model):
    """Cidadão com conta. O login é opcional: o site funciona sem ele.

    LGPD: guarda só o mínimo (e-mail e senha em hash) e a data em que a
    pessoa aceitou o termo de uso dos dados.

    Quando a pessoa exclui a conta, a linha não é apagada: os dados pessoais
    (e-mail e senha), os temas salvos e os lembretes são apagados, e a conta
    fica como "excluído" com a data do pedido. Assim o admin vê que o pedido
    foi atendido, sem saber de quem era a conta. Mesmo jeito do FacilMed.
    """
    __tablename__ = "usuario"
    __table_args__ = (
        db.CheckConstraint(
            "status IN ('ativo', 'bloqueado', 'excluido')", name="ck_usuario_status"
        ),
        # Trava no próprio banco: conta excluída fica excluída para sempre
        # (nem um "desbloquear" do admin consegue reativar).
        db.CheckConstraint(
            "excluida_em IS NULL OR status = 'excluido'", name="ck_usuario_excluida"
        ),
    )

    id = db.Column(db.Integer, primary_key=True)
    # E-mail e senha ficam vazios depois da exclusão. Vários NULL não ferem o
    # UNIQUE, então a pessoa pode criar uma conta nova com o mesmo e-mail.
    email = db.Column(db.String(150), unique=True)
    senha_hash = db.Column(db.String(255))
    consentimento_em = db.Column(db.DateTime, nullable=False)
    criado_em = db.Column(db.DateTime, nullable=False, default=datetime.now)

    status = db.Column(db.String(20), nullable=False, default=ATIVO, index=True)
    # O motivo do bloqueio é interno: a pessoa só vê que a conta está bloqueada.
    motivo_bloqueio = db.Column(db.String(255))
    bloqueado_por_id = db.Column(
        db.Integer, db.ForeignKey("administrador.id", ondelete="SET NULL")
    )
    bloqueado_em = db.Column(db.DateTime)
    excluida_em = db.Column(db.DateTime)

    # A exclusão em cascata é feita pelo próprio ORM (sem passive_deletes),
    # porque o SQLite dos testes não aplica o ON DELETE CASCADE sozinho.
    acompanhamentos = db.relationship(
        "Acompanhamento", back_populates="usuario",
        cascade="all, delete-orphan", order_by="Acompanhamento.criado_em.desc()",
    )
    lembretes = db.relationship(
        "Lembrete", back_populates="usuario",
        cascade="all, delete-orphan", order_by="Lembrete.data",
    )
    # As denúncias continuam depois que a conta é excluída, mas sem dono.
    denuncias = db.relationship("LinkDenunciado", back_populates="usuario")
    bloqueado_por = db.relationship("Administrador")

    def definir_senha(self, senha):
        self.senha_hash = generate_password_hash(senha)

    def conferir_senha(self, senha):
        return bool(self.senha_hash) and check_password_hash(self.senha_hash, senha)

    # ---------- Link de "esqueci minha senha" ----------
    # O link leva um token assinado com a SECRET_KEY (ninguém consegue inventar
    # um). Dentro dele vai o id da conta e um pedaço do hash da senha atual:
    # quando a senha muda, o pedaço muda e o link antigo para de funcionar.
    # Por isso o link só serve uma vez e não precisa de tabela nova no banco.

    @staticmethod
    def _assinador():
        return URLSafeTimedSerializer(current_app.config["SECRET_KEY"], salt="redefinir-senha")

    def gerar_token_senha(self):
        return Usuario._assinador().dumps({"id": self.id, "h": self.senha_hash[-16:]})

    @staticmethod
    def pelo_token_senha(token):
        """Devolve a conta dona do token, ou None se o link for inválido, vencido ou já usado."""
        try:
            dados = Usuario._assinador().loads(
                token, max_age=current_app.config["VALIDADE_LINK_SENHA"]
            )
        except BadSignature:  # inclui o SignatureExpired (link vencido)
            return None
        usuario = db.session.get(Usuario, dados.get("id"))
        if (usuario is None or not usuario.esta_ativo or not usuario.senha_hash
                or usuario.senha_hash[-16:] != dados.get("h")):
            return None
        return usuario

    @property
    def esta_ativo(self):
        return self.status == ATIVO

    @property
    def foi_excluida(self):
        return self.excluida_em is not None

    def bloquear(self, motivo, administrador):
        self.status = BLOQUEADO
        self.motivo_bloqueio = motivo
        self.bloqueado_por = administrador
        self.bloqueado_em = datetime.now()

    def desbloquear(self):
        self.status = ATIVO
        self.motivo_bloqueio = None
        self.bloqueado_por = None
        self.bloqueado_em = None

    def excluir_conta(self):
        """Pedido de exclusão do titular (LGPD): apaga os dados pessoais e mantém o registro."""
        self.acompanhamentos.clear()   # delete-orphan apaga do banco
        self.lembretes.clear()
        for denuncia in self.denuncias:
            denuncia.usuario = None
        self.email = None
        self.senha_hash = None
        self.motivo_bloqueio = None
        self.bloqueado_por = None
        self.bloqueado_em = None
        self.status = EXCLUIDO
        self.excluida_em = datetime.now()

    def __repr__(self):
        return f"<Usuario {self.id}>"
