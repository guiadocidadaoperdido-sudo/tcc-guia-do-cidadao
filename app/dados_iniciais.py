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

# Temas acrescentados em 22/10/2026, a partir dos assuntos mais pedidos na
# pesquisa de campo (seção 3.2): documentos, trabalho, saúde e educação.
CATEGORIAS += [
    {
        "nome": "Documentos",
        "slug": "documentos",
        "descricao": "Identidade e outros documentos pessoais.",
    },
    {
        "nome": "Trabalho",
        "slug": "trabalho",
        "descricao": "Carteira de trabalho, seguro-desemprego e direitos de quem trabalha.",
    },
    {
        "nome": "Saúde",
        "slug": "saude",
        "descricao": "Atendimento pelo SUS e cartão de saúde.",
    },
    {
        "nome": "Educação",
        "slug": "educacao",
        "descricao": "Enem e formas de entrar na faculdade.",
    },
]

CONTEUDOS += [
    {
        "categoria": "documentos",
        "titulo": "Carteira de Identidade Nacional (CIN)",
        "slug": "carteira-de-identidade-nacional",
        "resumo": "A nova carteira de identidade usa o número do CPF em todo o país. "
                  "A primeira via é gratuita e também fica disponível no aplicativo gov.br.",
        "o_que_e": (
            "A Carteira de Identidade Nacional (CIN) é o novo modelo de RG. Ela tem o mesmo "
            "padrão em todos os estados e usa o número do CPF como número de registro. Assim, "
            "a pessoa passa a ter um único número de identidade no Brasil inteiro.\n\n"
            "Depois de receber o documento impresso, a pessoa também pode usar a versão digital "
            "da carteira no aplicativo gov.br.\n\n"
            "O RG no modelo antigo continua valendo até 28 de fevereiro de 2032. Não é preciso "
            "correr para trocar, mas quem for tirar a primeira identidade ou a renovação já recebe "
            "o modelo novo."
        ),
        "quem_tem_direito": (
            "Qualquer pessoa, de qualquer idade.\n"
            "A primeira via e a renovação são gratuitas. A segunda via (por perda, por exemplo) pode ter taxa, que é definida por cada estado.\n"
            "Validade: 5 anos para crianças até 12 anos incompletos; 10 anos de 12 a 60 anos incompletos; sem prazo para quem tem mais de 60 anos."
        ),
        "documentos": (
            "Certidão de nascimento ou de casamento (original)\n"
            "Número do CPF (se ainda não tiver, em geral é possível fazer na hora)\n"
            "Outros documentos que o órgão de identificação do seu estado pedir no agendamento"
        ),
        "como_solicitar": (
            "Procure o órgão de identificação do seu estado (em São Paulo, o atendimento é pelo Poupatempo).\n"
            "Faça o agendamento pelo site ou aplicativo do órgão estadual.\n"
            "No dia marcado, leve os documentos originais. A foto e as digitais são tiradas no atendimento.\n"
            "Retire a carteira no prazo informado pelo posto.\n"
            "Depois da entrega, ative a versão digital no aplicativo gov.br."
        ),
        "alerta_golpes": (
            "A primeira via é gratuita. Desconfie de sites que cobram para \"agendar\" ou \"liberar\" "
            "a nova identidade. Agende só pelo site do órgão de identificação do seu estado ou pelo gov.br."
        ),
        "fontes": [
            {
                "orgao": "Ministério da Gestão e da Inovação em Serviços Públicos",
                "titulo": "Perguntas e respostas sobre a nova Carteira de Identidade Nacional",
                "url": "https://www.gov.br/gestao/pt-br/identidade-nacional",
            },
        ],
    },
    {
        "categoria": "trabalho",
        "titulo": "Carteira de Trabalho Digital",
        "slug": "carteira-de-trabalho-digital",
        "resumo": "A carteira de trabalho agora é digital: basta ter CPF e conta gov.br para "
                  "ver seus empregos e contratos no celular. É gratuita.",
        "o_que_e": (
            "A Carteira de Trabalho e Previdência Social (CTPS) registra a vida profissional da "
            "pessoa: empregos, salários, férias e outros dados que garantem os direitos trabalhistas.\n\n"
            "Hoje ela é emitida no formato digital. O número da carteira é o próprio CPF, e o "
            "empregador informa os dados do contrato pelo sistema do governo. A carteira de papel "
            "só é usada, em casos excepcionais, para anotar empregos antigos, de antes do modelo digital."
        ),
        "quem_tem_direito": (
            "Qualquer pessoa que tenha CPF.\n"
            "O serviço é gratuito."
        ),
        "documentos": (
            "Número do CPF\n"
            "Conta gov.br (nível bronze, prata ou ouro)"
        ),
        "como_solicitar": (
            "Baixe o aplicativo Carteira de Trabalho Digital (Android ou iPhone) ou acesse a versão pela internet.\n"
            "Entre com a sua conta gov.br.\n"
            "Pronto: a carteira é liberada na hora. Confira se os seus empregos aparecem corretamente.\n"
            "Se algum dado estiver errado, fale com o empregador ou com o Ministério do Trabalho pelo telefone 158."
        ),
        "alerta_golpes": (
            "Tirar a carteira de trabalho é gratuito. O governo não cobra taxa nem pede pagamento "
            "por Pix para liberar a carteira ou \"valores esquecidos\". Use só o aplicativo oficial."
        ),
        "fontes": [
            {
                "orgao": "Ministério do Trabalho e Emprego",
                "titulo": "Obter a Carteira de Trabalho",
                "url": "https://www.gov.br/pt-br/servicos/obter-a-carteira-de-trabalho",
            },
        ],
    },
    {
        "categoria": "trabalho",
        "titulo": "Seguro-desemprego",
        "slug": "seguro-desemprego",
        "resumo": "Ajuda em dinheiro, por alguns meses, para quem trabalhava com carteira "
                  "assinada e foi demitido sem justa causa.",
        "o_que_e": (
            "O seguro-desemprego é um benefício que paga, por um tempo, parcelas mensais ao "
            "trabalhador que foi dispensado sem justa causa. Ele serve para ajudar no sustento "
            "enquanto a pessoa procura um novo emprego.\n\n"
            "A quantidade e o valor das parcelas dependem do salário e do tempo trabalhado. "
            "Depois de pedir, é possível acompanhar valor, número de parcelas e datas pelo "
            "aplicativo Carteira de Trabalho Digital ou pelo gov.br."
        ),
        "quem_tem_direito": (
            "Quem foi demitido sem justa causa.\n"
            "Na 1ª vez que pede: ter recebido salário em pelo menos 12 dos últimos 18 meses antes da demissão.\n"
            "Na 2ª vez: pelo menos 9 dos últimos 12 meses.\n"
            "Da 3ª vez em diante: ter recebido salário em cada um dos 6 meses antes da demissão.\n"
            "Não ter outra renda suficiente para o sustento da família.\n"
            "Não receber benefício contínuo do INSS (com algumas exceções, como o auxílio-acidente)."
        ),
        "documentos": (
            "Requerimento do Seguro-Desemprego, entregue pelo empregador na demissão\n"
            "Número do CPF\n"
            "Conta gov.br (para pedir pela internet ou pelo aplicativo)\n"
            "Dados de uma conta bancária no seu nome (não vale conta salário nem conta conjunta)"
        ),
        "como_solicitar": (
            "Pegue com o empregador o requerimento do seguro-desemprego.\n"
            "Faça o pedido pelo aplicativo Carteira de Trabalho Digital, pelo portal de serviços do governo ou pelo telefone 158.\n"
            "Se preferir atendimento presencial, agende no posto indicado pelo Ministério do Trabalho.\n"
            "Informe uma conta bancária no seu nome para receber.\n"
            "Acompanhe a liberação das parcelas pelo aplicativo ou pelo gov.br."
        ),
        "alerta_golpes": (
            "O pedido é gratuito. Ninguém pode cobrar para \"adiantar\" ou \"liberar\" o seguro-desemprego. "
            "Desconfie de mensagens com links e de quem pede sua senha do gov.br."
        ),
        "fontes": [
            {
                "orgao": "Ministério do Trabalho e Emprego",
                "titulo": "Solicitar o Seguro-Desemprego",
                "url": "https://www.gov.br/pt-br/servicos/solicitar-o-seguro-desemprego",
            },
        ],
    },
    {
        "categoria": "saude",
        "titulo": "Cartão SUS (Cartão Nacional de Saúde)",
        "slug": "cartao-sus",
        "resumo": "O Cartão SUS identifica você no atendimento de saúde pública. O cadastro é "
                  "feito numa unidade de saúde, e o cartão digital fica no app Meu SUS Digital.",
        "o_que_e": (
            "O Cartão Nacional de Saúde, conhecido como Cartão SUS, tem um número que identifica "
            "cada pessoa no Sistema Único de Saúde. Com ele, os atendimentos, as vacinas e os "
            "exames ficam ligados ao seu cadastro.\n\n"
            "O cartão novo é feito de forma presencial, em um estabelecimento de saúde. Depois, "
            "você pode ver o cartão no celular pelo aplicativo Meu SUS Digital, que mostra o número, "
            "a foto e um QR Code.\n\n"
            "Algumas pessoas têm mais de um número de cartão. Os números que começam com 7 são o "
            "cadastro principal usado pelos sistemas do SUS."
        ),
        "quem_tem_direito": (
            "Qualquer pessoa que use o SUS, de qualquer idade.\n"
            "O cartão é gratuito."
        ),
        "documentos": (
            "Documento de identificação com foto (para crianças, a certidão de nascimento)\n"
            "CPF\n"
            "Comprovante de residência"
        ),
        "como_solicitar": (
            "Vá a uma Unidade Básica de Saúde (posto de saúde) perto da sua casa com os documentos.\n"
            "Peça o cadastro no Cartão Nacional de Saúde. O cartão impresso também é feito na unidade.\n"
            "Para ter o cartão no celular, baixe o aplicativo Meu SUS Digital e entre com a sua conta gov.br.\n"
            "No aplicativo, abra o Perfil e toque no ícone do cartão para ver o número e o QR Code.\n"
            "Mudou de endereço ou outro dado? Atualize na unidade de saúde."
        ),
        "alerta_golpes": (
            "O Cartão SUS é gratuito. O SUS não cobra para fazer o cartão nem para marcar consultas. "
            "Use só o aplicativo oficial Meu SUS Digital."
        ),
        "fontes": [
            {
                "orgao": "Ministério da Saúde",
                "titulo": "Meu SUS Digital: perguntas e respostas",
                "url": "https://www.gov.br/saude/pt-br/composicao/seidigi/meususdigital/perguntas-e-respostas/cidadao",
            },
            {
                "orgao": "Ministério da Saúde",
                "titulo": "Meu SUS Digital",
                "url": "https://www.gov.br/saude/pt-br/composicao/seidigi/meususdigital",
            },
        ],
    },
    {
        "categoria": "educacao",
        "titulo": "Enem (Exame Nacional do Ensino Médio)",
        "slug": "enem",
        "resumo": "A nota do Enem serve para entrar na faculdade pelo Sisu e pelo Prouni e para "
                  "pedir o Fies. Quem estuda em escola pública ou está no CadÚnico pode ter isenção da taxa.",
        "o_que_e": (
            "O Enem é uma prova do Governo Federal, feita pelo Inep, que avalia o que o estudante "
            "aprendeu no ensino médio. A nota é usada para concorrer a vagas em faculdades públicas "
            "pelo Sisu, a bolsas em faculdades privadas pelo Prouni e para pedir o financiamento "
            "estudantil (Fies).\n\n"
            "A prova acontece em dois domingos seguidos: no primeiro, linguagens, redação e ciências "
            "humanas; no segundo, matemática e ciências da natureza.\n\n"
            "As datas, a taxa e as regras mudam a cada ano e ficam no edital, publicado no site do Inep."
        ),
        "quem_tem_direito": (
            "Qualquer pessoa pode fazer o Enem.\n"
            "Quem ainda não vai terminar o ensino médio no ano da prova faz como \"treineiro\": a nota serve só para treinar.\n"
            "Isenção da taxa: quem está no último ano do ensino médio em escola pública.\n"
            "Isenção da taxa: quem fez todo o ensino médio em escola pública (ou com bolsa integral em escola privada) e tem renda por pessoa de até um salário mínimo e meio.\n"
            "Isenção da taxa: quem está no Cadastro Único, com NIS, dentro do limite de renda do edital."
        ),
        "documentos": (
            "CPF\n"
            "Conta gov.br (bronze, prata ou ouro) para entrar na Página do Participante\n"
            "No dia da prova: documento oficial de identificação com foto, original e válido\n"
            "No dia da prova: caneta esferográfica de tinta preta, de material transparente\n"
            "Cartão de Confirmação da Inscrição (recomendado, não obrigatório)"
        ),
        "como_solicitar": (
            "Se tiver direito, peça a isenção da taxa na Página do Participante, no prazo do edital.\n"
            "Faça a inscrição na Página do Participante (enem.inep.gov.br/participante). Mesmo quem tem isenção precisa se inscrever.\n"
            "Se não tiver isenção, pague o boleto (GRU) gerado no fim da inscrição, dentro do prazo.\n"
            "Cerca de três semanas antes da prova, veja o Cartão de Confirmação com o local da prova.\n"
            "Faça a prova nos dois domingos e depois acompanhe o resultado na Página do Participante."
        ),
        "alerta_golpes": (
            "A inscrição é feita só na Página do Participante do Inep. Desconfie de sites e mensagens "
            "que cobram para inscrever, prometem \"vazar\" a prova ou pedem sua senha do gov.br. "
            "Print ou foto do documento não vale no dia da prova."
        ),
        "fontes": [
            {
                "orgao": "Inep",
                "titulo": "Fazer o Exame Nacional do Ensino Médio (Enem)",
                "url": "https://www.gov.br/pt-br/servicos/fazer-o-exame-nacional-do-ensino-medio",
            },
            {
                "orgao": "Inep",
                "titulo": "Enem",
                "url": "https://www.gov.br/inep/pt-br/areas-de-atuacao/avaliacao-e-exames-educacionais/enem",
            },
        ],
    },
]
