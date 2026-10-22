# Guia do Cidadão Perdido

Sistema web que reúne e explica, em linguagem simples, informações sobre direitos, deveres e serviços públicos, sempre com link para a fonte oficial.

Trabalho de Conclusão de Curso do Técnico em Desenvolvimento de Sistemas, Etec Profª Ilza Nascimento Pintus (Centro Paula Souza), São José dos Campos - SP, 2026.

## Autores
- Sidney Campos
- Vitor Gabriel

Orientador: Prof. Jean Carlos Lourenço Costa

## Temas iniciais
| Tema | Conteúdos |
|---|---|
| Assistência social | Bolsa Família |
| Moradia | Minha Casa, Minha Vida |
| Serviço militar | Alistamento militar |
| Trânsito e habilitação | Primeira habilitação (CNH) |
| Documentos | Carteira de Identidade Nacional (CIN) |
| Trabalho | Carteira de Trabalho Digital, Seguro-desemprego |
| Saúde | Cartão SUS |
| Educação | Enem |

Os quatro últimos temas vieram dos assuntos mais pedidos na pesquisa de campo (seção 3.2 do TCC).

## Funcionalidades
**Para o cidadão (sem cadastro)**
- Temas, busca por palavra (pesquisa em português no PostgreSQL) e busca instantânea enquanto digita.
- Cada conteúdo em partes: o que é, quem tem direito, documentos, passo a passo, alerta de golpes e fontes oficiais.
- Checklist de documentos para marcar o que já separou (fica só no aparelho), imprimir e compartilhar.
- "Veja também" com conteúdos do mesmo tema; "Este conteúdo foi útil?" com sugestão opcional.
- Barra de acessibilidade: tamanho da letra e alto contraste; atalho "Ir para o conteúdo" (tecla de acesso 1).
- Aplicativo instalável (PWA): pode ser adicionado à tela inicial do celular e abre as páginas já visitadas sem internet.

**Para a equipe (área administrativa)**
- Login com limite de tentativas, cadastro de temas, conteúdos e fontes oficiais, publicação/rascunho e relatório das avaliações.

**Para outros sistemas**
- API REST somente leitura em JSON (ver abaixo).

## Tecnologias
- HTML, CSS e JavaScript (interface)
- Python com Flask, Jinja2, Flask-SQLAlchemy, Flask-Login, Flask-WTF, Flask-Migrate (Alembic) e Flask-Limiter (servidor)
- PostgreSQL (banco de dados), com psycopg
- pytest e GitHub Actions (testes automáticos a cada push)
- Gunicorn, Render (site) e Neon (banco) na nuvem

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
4. Criar as tabelas (aplicando as migrações), cadastrar os conteúdos iniciais e o primeiro administrador:
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

## Banco de dados e migrações
As tabelas são criadas e alteradas por **migrações** (Flask-Migrate/Alembic), na pasta `migrations/`. A migração `0001` cria as cinco tabelas do Apêndice B e o índice da busca.

- `flask --app run criar-banco` aplica as migrações que faltam. Bancos criados antes das migrações são reconhecidos e marcados automaticamente.
- Mudou um model? Gere a migração e confira o arquivo antes de aplicar:
  ```
  flask --app run db migrate -m "descreva a mudança"
  flask --app run criar-banco
  ```
- No Render, o `criar-banco` roda a cada publicação (veja `render.yaml`), então a migração chega ao Neon sozinha.

## API REST (somente leitura)
Entrega só conteúdos publicados, em JSON. Não exige login e não expõe rascunhos, avaliações nem dados de administradores.

| Endereço | O que devolve |
|---|---|
| `GET /api/v1/categorias` | Temas com o total de conteúdos |
| `GET /api/v1/conteudos?q=&categoria=&limite=` | Lista (com busca e filtro por tema; limite até 50) |
| `GET /api/v1/conteudos/<slug>` | Conteúdo completo, com partes e fontes oficiais |

Exemplo: `curl https://SEU-SITE.onrender.com/api/v1/conteudos?q=cnh`

## Segurança e operação
- Limite de tentativas: 5 logins por minuto (20 por hora) e 30 avaliações por hora por IP. O IP fica só na memória do servidor.
- Registros (logs) das ações da área administrativa e dos erros, sem dados de visitantes. No Render, aparecem na aba Logs.
- `GET /saude` responde `{"status": "ok", "banco": "ok"}` quando o site e o banco funcionam. O Render usa esse endereço para saber se o site está no ar.
- Fontes servidas pelo próprio site e Content-Security-Policy sem serviços de terceiros: nenhum dado do visitante vai para outras empresas.

## Testes
Os casos de teste CT01 a CT12 do TCC (Quadro 8), os testes de segurança e os das funções do MVP (API, PWA, limite de tentativas, migrações) estão em `tests/`.
```
python -m pytest
```
Por padrão os testes usam um banco SQLite em memória. Para rodar no PostgreSQL, crie um banco vazio só para testes e defina `TEST_DATABASE_URL` (ex.: `postgresql://postgres:SENHA@localhost:5432/guia_testes`). Nesse caso também roda o teste da busca em português ("documentos" encontra "documento").

No GitHub, o workflow `.github/workflows/testes.yml` roda os testes no SQLite e no PostgreSQL a cada push na `main` e confere as migrações.

## Estrutura de pastas
```
app/
  __init__.py      create_app: monta a aplicação e liga as extensões
  controllers/     rotas do Flask: publico.py (parte pública), admin.py (área restrita) e api.py (API JSON)
  models/          classes ligadas às cinco tabelas do banco
  templates/       páginas HTML em Jinja2 (publico/, admin/, erros/)
  static/          css/, js/ (main.js e sw.js do PWA), img/, fonts/ e manifest.webmanifest
  forms.py         formulários da área administrativa (com proteção CSRF)
  cli.py           comandos criar-banco, dados-iniciais e criar-admin
  dados_iniciais.py  categorias e conteúdos iniciais
migrations/        migrações do banco (Flask-Migrate/Alembic)
.github/workflows/ testes automáticos no GitHub Actions
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
| RNF01, RNF02 | CSS feito primeiro para o celular; contraste, foco visível, barra de acessibilidade (letra e alto contraste), rótulos nos campos |
| RNF04 | Hash da senha com Werkzeug |
| RNF05 | Consultas pelo SQLAlchemy, sempre parametrizadas |
| RNF06 | Flask-WTF (token CSRF em todos os formulários) |
| RNF07 | `COOKIE_SEGURO=1` no `.env` ativa cookies seguros e o cabeçalho HSTS quando publicado com HTTPS |
| RNF10 | Nenhum dado pessoal do visitante é salvo; fontes e scripts só do próprio site |

## Aviso
O Guia do Cidadão Perdido é informativo. Não executa nem substitui os procedimentos dos órgãos públicos.
Os textos iniciais foram escritos a partir das páginas oficiais consultadas em outubro de 2026. Regras e valores mudam: confira cada conteúdo na fonte oficial antes de apresentar o sistema.
