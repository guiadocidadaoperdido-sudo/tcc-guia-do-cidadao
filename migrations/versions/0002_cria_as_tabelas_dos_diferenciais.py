"""cria as tabelas dos diferenciais (conta, acompanhamento, lembretes, denúncias e glossário)

Revision ID: 0002
Revises: 0001
Create Date: 2026-10-23

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0002'
down_revision = '0001'
branch_labels = None
depends_on = None


def upgrade():
    # Glossário "O que é isso?"
    op.create_table('termo_glossario',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('termo', sa.String(length=80), nullable=False),
    sa.Column('explicacao', sa.String(length=400), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('termo')
    )

    # Conta do cidadão (login opcional, LGPD: só e-mail, senha em hash e consentimento).
    # Situação: ativo, bloqueado (pelo admin) ou excluido (pelo próprio cidadão;
    # e-mail e senha ficam vazios e a conta não volta).
    op.create_table('usuario',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('email', sa.String(length=150), nullable=True),
    sa.Column('senha_hash', sa.String(length=255), nullable=True),
    sa.Column('consentimento_em', sa.DateTime(), nullable=False),
    sa.Column('criado_em', sa.DateTime(), nullable=False),
    sa.Column('status', sa.String(length=20), nullable=False),
    sa.Column('motivo_bloqueio', sa.String(length=255), nullable=True),
    sa.Column('bloqueado_por_id', sa.Integer(), nullable=True),
    sa.Column('bloqueado_em', sa.DateTime(), nullable=True),
    sa.Column('excluida_em', sa.DateTime(), nullable=True),
    sa.CheckConstraint("status IN ('ativo', 'bloqueado', 'excluido')", name='ck_usuario_status'),
    sa.CheckConstraint("excluida_em IS NULL OR status = 'excluido'", name='ck_usuario_excluida'),
    sa.ForeignKeyConstraint(['bloqueado_por_id'], ['administrador.id'], ondelete='SET NULL'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('email')
    )
    op.create_index('ix_usuario_status', 'usuario', ['status'])

    # Links suspeitos denunciados (o admin revisa)
    op.create_table('link_denunciado',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('usuario_id', sa.Integer(), nullable=True),
    sa.Column('administrador_id', sa.Integer(), nullable=True),
    sa.Column('url', sa.String(length=500), nullable=False),
    sa.Column('dominio', sa.String(length=255), nullable=False),
    sa.Column('descricao', sa.String(length=500), nullable=True),
    sa.Column('status', sa.String(length=20), nullable=False),
    sa.Column('criado_em', sa.DateTime(), nullable=False),
    sa.Column('revisado_em', sa.DateTime(), nullable=True),
    sa.CheckConstraint("status IN ('pendente', 'confirmado', 'descartado')", name='ck_link_denunciado_status'),
    sa.ForeignKeyConstraint(['administrador_id'], ['administrador.id'], ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['usuario_id'], ['usuario.id'], ondelete='SET NULL'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_link_denunciado_dominio', 'link_denunciado', ['dominio'])
    op.create_index('ix_link_denunciado_status', 'link_denunciado', ['status'])

    # Temas salvos pelo cidadão, com o passo atual e o checklist
    op.create_table('acompanhamento',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('usuario_id', sa.Integer(), nullable=False),
    sa.Column('conteudo_id', sa.Integer(), nullable=False),
    sa.Column('passo_atual', sa.Integer(), nullable=False),
    sa.Column('documentos_marcados', sa.JSON(), nullable=False),
    sa.Column('visto_em', sa.DateTime(), nullable=False),
    sa.Column('criado_em', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['conteudo_id'], ['conteudo.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['usuario_id'], ['usuario.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('usuario_id', 'conteudo_id', name='uq_acompanhamento_usuario_conteudo')
    )

    # Lembretes de prazo (vão para a agenda do Google, Outlook ou iPhone)
    op.create_table('lembrete',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('usuario_id', sa.Integer(), nullable=False),
    sa.Column('conteudo_id', sa.Integer(), nullable=True),
    sa.Column('titulo', sa.String(length=150), nullable=False),
    sa.Column('data', sa.Date(), nullable=False),
    sa.Column('criado_em', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['conteudo_id'], ['conteudo.id'], ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['usuario_id'], ['usuario.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )


def downgrade():
    op.drop_table('lembrete')
    op.drop_table('acompanhamento')
    op.drop_index('ix_link_denunciado_status', table_name='link_denunciado')
    op.drop_index('ix_link_denunciado_dominio', table_name='link_denunciado')
    op.drop_table('link_denunciado')
    op.drop_index('ix_usuario_status', table_name='usuario')
    op.drop_table('usuario')
    op.drop_table('termo_glossario')
