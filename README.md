# Guia do Cidadão Perdido

Sistema web que reúne e explica, em linguagem simples, informações sobre direitos, deveres e serviços públicos, sempre com link para a fonte oficial.

Trabalho de Conclusão de Curso do Técnico em Desenvolvimento de Sistemas, Etec Profª Ilza Nascimento Pintus (Centro Paula Souza), São José dos Campos - SP, 2026.

## Autores
- Sidney Campos
- Vitor Gabriel

Orientador: Prof. Jean Carlos Lourenco Costa

## Temas iniciais
- Bolsa Família
- Minha Casa, Minha Vida
- Alistamento militar
- CNH (Carteira Nacional de Habilitação)

## Tecnologias
- HTML, CSS e JavaScript (interface)
- Python com Flask (servidor)
- PostgreSQL (banco de dados)

## Estrutura de pastas
```
app/
  controllers/   rotas do Flask (recebem o pedido e escolhem a resposta)
  models/        acesso ao banco de dados
  templates/     páginas HTML
  static/        arquivos fixos: css/, js/ e img/
database/        scripts SQL (criação das tabelas e dados iniciais)
docs/
  diagramas/     UML e DER
  prototipos/    protótipos de telas
tests/           testes do sistema
```

## Aviso
O Guia do Cidadão Perdido é informativo. Não executa nem substitui os procedimentos dos órgãos públicos.
