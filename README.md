# Guia do Cidadão Perdido

Sistema web que reúne e explica, em linguagem simples, informações sobre direitos, deveres e serviços públicos, sempre com link para a fonte oficial.

Trabalho de Conclusão de Curso do Técnico em Desenvolvimento de Sistemas, Etec Profª Ilza Nascimento Pintus (Centro Paula Souza), São José dos Campos - SP, 2026.

## Autores
- Sidney Campos
- Vitor Gabriel

Orientador: Prof. Jean Carlos Lourenço Costa

## Temas iniciais
- Bolsa Família
- Minha Casa, Minha Vida
- Alistamento militar
- CNH (Carteira Nacional de Habilitação)

## Tecnologias
- HTML, CSS e JavaScript (interface)
- Python com Flask, Jinja2, Flask-SQLAlchemy, Flask-Login e Flask-WTF (servidor)
- PostgreSQL (banco de dados), com psycopg

## Como rodar no computador

Precisa do Python 3.12 ou mais novo e do PostgreSQL instalados.

1. Criar o ambiente virtual e instalar as bibliotecas (dentro da pasta `guia-do-cidadao-perdido`):
   ```
   python -m venv .venv
   .venv\Scripts\activate
   pip install -r requirements.txt
   ```
2. Criar o banco no PostgreSQL (vai pedir a senha do usuário `postgres`):
   ```
   createdb -U postgres guia_cidadao
   ```
3. Copiar `.env.example` para `.env` e trocar a senha do banco e a `SECRET_KEY`.
   Sem o `.env`, o sistema usa um arquivo SQLite em `instance/guia.db` (a busca fica mais simples, sem a pesquisa em português).
4. Criar as tabelas, cadastrar os conteúdos iniciais e o primeiro administrador:
   ```
   flask --app run criar-banco
   flask --app run dados-iniciais
   flask --app run criar-admin
   ```
5. Rodar o site:
   ```
   python run.py
   ```
   Parte pública: http://localhost:5000 · Área administrativa: http://localhost:5000/admin

## Como publicar na nuvem (Render + Neon)

O site roda no Render e o banco PostgreSQL fica no Neon (plano grátis que não expira).

1. **Banco:** crie um projeto em https://neon.tech e copie o endereço de conexão (`postgresql://...`).
2. **Dados iniciais e administrador:** no computador, dentro desta pasta, aponte para o banco do Neon e rode os comandos (troque pelo endereço copiado):
   ```
   $env:DATABASE_URL="postgresql://...neon.tech/neondb?sslmode=require"
   .venv\Scripts\flask --app run criar-banco
   .venv\Scripts\flask --app run dados-iniciais
   .venv\Scripts\flask --app run criar-admin
   ```
   Feche o terminal depois, para voltar a usar o banco local do `.env`.
3. **GitHub:** envie esta pasta para um repositório no GitHub (o `.env` fica de fora).
4. **Render:** em https://dashboard.render.com, clique em **New > Blueprint**, escolha o repositório e, quando pedir, cole o endereço do Neon em `DATABASE_URL`. O arquivo `render.yaml` já configura o resto (gunicorn, chave secreta, HTTPS).
5. A cada `git push`, o Render publica a nova versão sozinho.

No plano grátis o site "dorme" depois de uns 15 minutos sem visitas; o primeiro acesso depois disso demora cerca de 1 minuto.

## Testes
Os casos de teste CT01 a CT12 do TCC (Quadro 8) e alguns testes de segurança estão em `tests/`.
```
python -m pytest
```
Por padrão os testes usam um banco SQLite em memória. Para rodar no PostgreSQL, crie um banco vazio só para testes e defina `TEST_DATABASE_URL` (ex.: `postgresql://postgres:SENHA@localhost:5432/guia_testes`). Nesse caso também roda o teste da busca em português ("documentos" encontra "documento").

## Estrutura de pastas
```
app/
  __init__.py      create_app: monta a aplicação e liga as extensões
  controllers/     rotas do Flask: publico.py (blueprint público) e admin.py (área restrita)
  models/          classes ligadas às cinco tabelas do banco
  templates/       páginas HTML em Jinja2 (publico/, admin/, erros/)
  static/          css/, js/ e img/
  forms.py         formulários da área administrativa (com proteção CSRF)
  cli.py           comandos criar-banco, dados-iniciais e criar-admin
  dados_iniciais.py  categorias e conteúdos iniciais
config.py          configurações (lê o arquivo .env)
run.py             ponto de entrada
database/          schema.sql (script do Apêndice B)
docs/
  diagramas/       UML e DER
  prototipos/      protótipos de telas
tests/             testes automatizados (pytest)
```

## Requisitos atendidos
| Requisito | Onde está |
|---|---|
| RF01, RF02 | `publico.inicio` e `publico.categoria` |
| RF03 | `Conteudo.buscar` (pesquisa de texto em português no PostgreSQL, índice `idx_conteudo_busca`) |
| RF04, RF05, RF06 | `templates/publico/conteudo.html` (blocos que abrem e fecham, fontes, data, alerta) |
| RF07 | `publico.avaliar` (sem cadastro; evita voto repetido pela sessão) |
| RF08 | `admin.login` com Flask-Login; todas as rotas `/admin` exigem login |
| RF09, RF11 | `admin.conteudo_form`, `conteudo_publicar`, `conteudo_excluir` (não salva sem fonte oficial) |
| RF10 | `admin.categoria_form`, `categoria_excluir` (não exclui categoria com conteúdos) |
| RF12 | `admin.avaliacoes` |
| RNF01, RNF02 | CSS feito primeiro para o celular; contraste, foco visível, link "Pular para o conteúdo", rótulos nos campos |
| RNF04 | Hash da senha com Werkzeug |
| RNF05 | Consultas pelo SQLAlchemy, sempre parametrizadas |
| RNF06 | Flask-WTF (token CSRF em todos os formulários) |
| RNF07 | `COOKIE_SEGURO=1` no `.env` ativa cookies seguros e o cabeçalho HSTS quando publicado com HTTPS |
| RNF10 | Nenhum dado pessoal do visitante é salvo |

## Aviso
O Guia do Cidadão Perdido é informativo. Não executa nem substitui os procedimentos dos órgãos públicos.
Os textos iniciais foram escritos a partir das páginas oficiais consultadas em outubro de 2026. Regras e valores mudam: confira cada conteúdo na fonte oficial antes de apresentar o sistema.
