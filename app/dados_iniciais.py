"""Categorias e conteúdos iniciais do guia (etapa h da seção 3.7 do TCC).

Os textos foram escritos a partir das páginas oficiais listadas em "fontes",
consultadas em outubro de 2026. Regras e valores mudam: antes de apresentar
o sistema, confira cada texto na fonte oficial e atualize pela área
administrativa.

Formato dos campos: em "o_que_e", parágrafos separados por linha em branco;
em "quem_tem_direito", "documentos" e "como_solicitar", um item por linha.
"""

CATEGORIAS = [
    {
        "nome": "Assistência social",
        "slug": "assistencia-social",
        "descricao": "Programas de transferência de renda e apoio às famílias.",
    },
    {
        "nome": "Moradia",
        "slug": "moradia",
        "descricao": "Programas para conseguir a casa própria.",
    },
    {
        "nome": "Serviço militar",
        "slug": "servico-militar",
        "descricao": "Alistamento e regularização da situação militar.",
    },
    {
        "nome": "Trânsito e habilitação",
        "slug": "transito-e-habilitacao",
        "descricao": "Carteira de motorista e outros serviços de trânsito.",
    },
]

CONTEUDOS = [
    {
        "categoria": "assistencia-social",
        "titulo": "Bolsa Família",
        "slug": "bolsa-familia",
        "resumo": "Programa do Governo Federal que paga um valor todo mês para famílias "
                  "de baixa renda. Para receber, a família precisa estar no Cadastro Único.",
        "o_que_e": (
            "O Bolsa Família é um programa do Governo Federal que transfere dinheiro, "
            "todo mês, para famílias em situação de pobreza. O objetivo é garantir uma "
            "renda básica e ajudar a família a ter acesso a saúde, educação e "
            "assistência social.\n\n"
            "O valor que cada família recebe depende de quantas pessoas moram na casa "
            "e de quem são essas pessoas. Famílias com crianças pequenas, gestantes e "
            "adolescentes recebem valores adicionais. O pagamento é feito pela Caixa.\n\n"
            "Para continuar recebendo, a família precisa cumprir alguns compromissos, "
            "como manter as crianças na escola, a vacinação em dia e o acompanhamento "
            "de saúde das gestantes."
        ),
        "quem_tem_direito": (
            "Famílias com renda por pessoa de até R$ 218 por mês.\n"
            "Para calcular, some tudo o que a família ganha no mês e divida pelo número de pessoas da casa.\n"
            "A família precisa estar inscrita no Cadastro Único, com os dados atualizados."
        ),
        "documentos": (
            "CPF ou título de eleitor da pessoa responsável pela família\n"
            "Documento de cada pessoa da família (certidão de nascimento ou casamento, RG, CPF ou carteira de trabalho)\n"
            "Comprovante de endereço, se tiver\n"
            "Comprovante de matrícula escolar das crianças e adolescentes, se tiver"
        ),
        "como_solicitar": (
            "Procure o CRAS (Centro de Referência de Assistência Social) ou o posto do Cadastro Único da sua cidade.\n"
            "Faça ou atualize a inscrição da família no Cadastro Único, levando os documentos de todos da casa.\n"
            "Aguarde: a seleção para o Bolsa Família é feita pelo Governo Federal, de forma automática, a partir dos dados do Cadastro Único.\n"
            "Acompanhe a situação pelo aplicativo Bolsa Família, pelo aplicativo Caixa Tem ou pelo telefone 121 (Disque Social).\n"
            "Mantenha o cadastro atualizado sempre que mudar a renda, o endereço ou as pessoas da casa."
        ),
        "alerta_golpes": (
            "A inscrição no Cadastro Único e no Bolsa Família é gratuita. Ninguém pode cobrar "
            "para incluir sua família no programa. Desconfie de mensagens, ligações ou sites que "
            "pedem pagamento, senha ou código recebido por SMS. Use só os aplicativos oficiais."
        ),
        "fontes": [
            {
                "orgao": "Ministério do Desenvolvimento e Assistência Social (MDS)",
                "titulo": "Bolsa Família",
                "url": "https://www.gov.br/mds/pt-br/acoes-e-programas/bolsa-familia",
            },
            {
                "orgao": "Ministério do Desenvolvimento e Assistência Social (MDS)",
                "titulo": "Bolsa Família: conheça as regras",
                "url": "https://www.gov.br/mds/pt-br/acoes-e-programas/bolsa-familia/conheca-as-regras",
            },
            {
                "orgao": "Ministério do Desenvolvimento e Assistência Social (MDS)",
                "titulo": "Cadastro Único",
                "url": "https://www.gov.br/mds/pt-br/acoes-e-programas/cadastro-unico",
            },
        ],
    },
    {
        "categoria": "moradia",
        "titulo": "Minha Casa, Minha Vida",
        "slug": "minha-casa-minha-vida",
        "resumo": "Programa do Governo Federal que ajuda famílias a comprar a casa própria, "
                  "com descontos e juros menores, conforme a renda da família.",
        "o_que_e": (
            "O Minha Casa, Minha Vida é um programa de moradia (habitacional) do Governo Federal. Ele ajuda "
            "famílias a conseguir a casa própria, com parcelas que cabem no orçamento.\n\n"
            "As famílias são divididas em faixas, de acordo com a renda mensal. Nas faixas de "
            "renda mais baixa, parte do valor do imóvel pode ser paga pelo governo (subsídio). "
            "Nas outras faixas, a família financia o imóvel com juros menores que os do mercado.\n\n"
            "Os valores de cada faixa mudam de tempos em tempos. Confira os valores atuais na "
            "página oficial do programa antes de procurar o atendimento."
        ),
        "quem_tem_direito": (
            "Famílias que moram em área urbana ou rural e se encaixam em uma das faixas de renda do programa.\n"
            "Em geral, a família não pode ter outro imóvel nem ter recebido outro benefício habitacional do governo.\n"
            "Nas faixas com subsídio, têm prioridade, por exemplo, famílias chefiadas por mulheres, com pessoas com deficiência, idosos ou em situação de risco."
        ),
        "documentos": (
            "RG e CPF de todas as pessoas que vão comprar o imóvel\n"
            "Comprovante de estado civil (certidão de nascimento, casamento ou união estável)\n"
            "Comprovante de renda de quem trabalha\n"
            "Comprovante de residência\n"
            "Número de inscrição no Cadastro Único, para quem for da faixa de renda mais baixa"
        ),
        "como_solicitar": (
            "Descubra em qual faixa de renda sua família está, na página oficial do programa.\n"
            "Faixa 1 com subsídio: procure a prefeitura da sua cidade ou uma entidade organizadora habilitada e faça a inscrição. Na faixa mais baixa, a família também precisa estar no Cadastro Único.\n"
            "Imóvel financiado: procure uma agência da Caixa ou do Banco do Brasil, ou um imóvel do programa em uma construtora parceira.\n"
            "Entregue os documentos e aguarde a análise de crédito e do cadastro.\n"
            "Se aprovado, assine o contrato no banco. Leia tudo antes de assinar."
        ),
        "alerta_golpes": (
            "É proibido cobrar taxa de cadastro ou taxa para \"furar a fila\" do Minha Casa, Minha Vida. "
            "Se alguém pedir dinheiro para incluir seu nome, não pague e denuncie ao Ministério Público "
            "ou pela plataforma Fala.BR."
        ),
        "fontes": [
            {
                "orgao": "Ministério das Cidades",
                "titulo": "Programa Minha Casa, Minha Vida",
                "url": "https://www.gov.br/cidades/pt-br/acesso-a-informacao/acoes-e-programas/habitacao/programa-minha-casa-minha-vida",
            },
            {
                "orgao": "Caixa Econômica Federal",
                "titulo": "Minha Casa Minha Vida",
                "url": "https://www.caixa.gov.br/voce/habitacao/minha-casa-minha-vida/Paginas/default.aspx",
            },
        ],
    },
    {
        "categoria": "servico-militar",
        "titulo": "Alistamento militar",
        "slug": "alistamento-militar",
        "resumo": "Todo brasileiro do sexo masculino precisa se alistar no ano em que completa "
                  "18 anos, de janeiro a junho. O alistamento pode ser feito pela internet.",
        "o_que_e": (
            "O alistamento militar é o primeiro passo do Serviço Militar Obrigatório. Ao se "
            "alistar, o jovem passa a concorrer à seleção para servir nas Forças Armadas "
            "(Exército, Marinha ou Aeronáutica).\n\n"
            "Depois do alistamento vem a seleção geral, com exames e entrevista. Quem for "
            "dispensado recebe o Certificado de Dispensa de Incorporação, que regulariza a "
            "situação militar. Quem for selecionado pode servir por cerca de 12 meses.\n\n"
            "Quem não se alista fica em débito com o serviço militar e pode ter problemas para "
            "tirar passaporte, fazer concurso público e assinar alguns contratos com o governo."
        ),
        "quem_tem_direito": (
            "Brasileiros do sexo masculino, no ano em que completam 18 anos.\n"
            "Brasileiros naturalizados ou por opção.\n"
            "Quem não se alistou no prazo também deve se alistar, mesmo com mais idade."
        ),
        "documentos": (
            "Certidão de nascimento (ou documento de naturalização ou de opção)\n"
            "Comprovante de residência ou declaração de residência assinada\n"
            "Documento oficial com foto"
        ),
        "como_solicitar": (
            "Entre no site oficial de alistamento do Exército (alistamento.eb.mil.br) entre 1º de janeiro e 30 de junho do ano em que você completa 18 anos.\n"
            "Preencha seus dados pessoais e anote o número do alistamento.\n"
            "Se preferir, ou se perdeu o prazo, vá à Junta de Serviço Militar da sua cidade com os documentos.\n"
            "Acompanhe no site a data e o local da seleção geral e compareça.\n"
            "Se for dispensado, pague a taxa militar (se houver), faça o juramento à Bandeira e retire seu certificado."
        ),
        "alerta_golpes": (
            "O alistamento é feito só no site oficial alistamento.eb.mil.br ou na Junta de Serviço "
            "Militar. Desconfie de sites e mensagens que cobram para fazer o alistamento por você "
            "ou que pedem pagamento por Pix fora dos canais oficiais."
        ),
        "fontes": [
            {
                "orgao": "Governo Federal (gov.br)",
                "titulo": "Alistar-se no Serviço Militar Obrigatório",
                "url": "https://www.gov.br/pt-br/servicos/alistar-se-no-servico-militar-obrigatorio",
            },
            {
                "orgao": "Exército Brasileiro",
                "titulo": "Alistamento militar on-line",
                "url": "https://alistamento.eb.mil.br/",
            },
        ],
    },
    {
        "categoria": "transito-e-habilitacao",
        "titulo": "Primeira habilitação (CNH)",
        "slug": "primeira-habilitacao-cnh",
        "resumo": "Como tirar a primeira Carteira Nacional de Habilitação (CNH) para moto ou carro. "
                  "Com o programa CNH do Brasil, a autoescola deixou de ser obrigatória.",
        "o_que_e": (
            "A Carteira Nacional de Habilitação (CNH) é o documento que permite dirigir. Na "
            "primeira habilitação, a pessoa pode tirar a categoria A (moto), a categoria B "
            "(carro) ou as duas juntas.\n\n"
            "Com o programa CNH do Brasil, do Ministério dos Transportes, o processo pode ser "
            "aberto pela internet, o curso teórico é gratuito pelo aplicativo e a autoescola "
            "deixou de ser obrigatória. A carga mínima de 20 horas de aulas práticas também "
            "não é mais exigida. A pessoa pode estudar sozinha, fazer aulas em uma autoescola "
            "ou contratar um instrutor autônomo autorizado pelo Detran.\n\n"
            "Mesmo assim, as provas teórica e prática continuam obrigatórias para todos. No "
            "começo, a pessoa recebe a Permissão para Dirigir, válida por um ano."
        ),
        "quem_tem_direito": (
            "Ter 18 anos completos.\n"
            "Saber ler e escrever.\n"
            "Ter CPF e um documento de identidade com foto."
        ),
        "documentos": (
            "Documento de identidade com foto\n"
            "CPF\n"
            "Comprovante de residência"
        ),
        "como_solicitar": (
            "Abra o processo pelo aplicativo CNH do Brasil ou pelo site do Ministério dos Transportes.\n"
            "Faça o curso teórico gratuito pelo aplicativo, ou estude em uma autoescola, se preferir.\n"
            "Vá ao Detran do seu estado para as etapas presenciais: coleta da biometria e exames médicos.\n"
            "Faça a prova teórica e, depois de aprovado, pratique com um instrutor autorizado ou em uma autoescola.\n"
            "Faça a prova prática de direção. Se for aprovado, você recebe a Permissão para Dirigir."
        ),
        "alerta_golpes": (
            "Existem sites e mensagens falsas sobre uma \"CNH gratuita\" que cobram taxa por Pix para "
            "fazer a inscrição. O processo é aberto só pelos canais oficiais do Governo Federal e do "
            "Detran do seu estado. Não pague taxas em sites que você não conhece."
        ),
        "fontes": [
            {
                "orgao": "Ministério dos Transportes",
                "titulo": "CNH do Brasil",
                "url": "https://www.gov.br/transportes/pt-br/cnh-do-brasil",
            },
            {
                "orgao": "Ministério dos Transportes",
                "titulo": "CNH do Brasil: saiba mais sobre o programa",
                "url": "https://www.gov.br/transportes/pt-br/conteudos-cnh-do-brasil/saiba-mais-sobre-o-programa",
            },
            {
                "orgao": "Centro Integrado de Segurança Cibernética (gov.br)",
                "titulo": "Falso programa de CNH cobra taxa via PIX",
                "url": "https://www.gov.br/cisc/pt-br/alertas-de-golpes-digitais/falso-programa-de-cnh-cobra-taxa-via-pix",
            },
        ],
    },
]
