from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone

from blog.models import BlogCategory, Post

User = get_user_model()


CATEGORIES = [
    ("Registro Civil", "registro-civil",
     "Artigos sobre certidões de nascimento, casamento, óbito e outros documentos do registro civil."),
    ("Certidões de Imóveis", "certidoes-de-imoveis",
     "Tudo sobre certidões do registro de imóveis: matrícula, ônus reais, inteiro teor e mais."),
    ("Protestos", "protestos",
     "Guias sobre certidões de protesto, consultas e regularização de títulos protestados."),
    ("Certidões Federais", "certidoes-federais",
     "Informações sobre certidões da Receita Federal, FGTS, débitos tributários e Justiça Federal."),
    ("Apostilamento", "apostilamento",
     "Como funciona a Apostila de Haia e como validar documentos brasileiros no exterior."),
    ("Segunda Via", "segunda-via",
     "Como obter a segunda via de certidões de nascimento, casamento, óbito e outros documentos."),
    ("Busca Patrimonial", "busca-patrimonial",
     "Orientações sobre busca de bens, pesquisa patrimonial e levantamento de ativos."),
    ("Cidadania", "cidadania",
     "Documentação para obtenção de cidadania italiana, portuguesa, espanhola e outras."),
    ("Cartórios", "cartorios",
     "Como funciona o sistema cartorial brasileiro: tipos, competências e serviços oferecidos."),
    ("Documentação", "documentacao",
     "Dicas gerais sobre organização e regularização de documentos pessoais e empresariais."),
]

ARTICLE_1_CONTENT = """
<h2>O que é a Certidão de Nascimento?</h2>
<p>A certidão de nascimento é o documento que registra oficialmente o nascimento de uma pessoa no Brasil. Emitida pelo Cartório de Registro Civil, ela é o ponto de partida para a obtenção de todos os demais documentos pessoais, como RG, CPF, passaporte e título de eleitor.</p>
<p>Sem a certidão de nascimento, é impossível exercer direitos básicos como votar, trabalhar formalmente, matricular-se em escolas ou acessar benefícios do governo.</p>

<h2>Quando Você Precisa de uma Segunda Via?</h2>
<p>A necessidade de uma segunda via pode surgir em diversas situações do cotidiano:</p>
<ul>
  <li>Perda ou extravio do documento original</li>
  <li>Deterioração por desgaste, umidade ou acidentes</li>
  <li>Atualização de dados após reconhecimento de paternidade</li>
  <li>Solicitação de passaporte ou documentos internacionais</li>
  <li>Processos judiciais ou administrativos que exigem documento recente</li>
  <li>Apostilamento para validade no exterior</li>
</ul>

<h2>Passo a Passo para Solicitar Online</h2>
<p>Com a modernização dos cartórios brasileiros, já é possível solicitar a segunda via da certidão de nascimento totalmente online, sem precisar sair de casa. Veja como:</p>
<h3>1. Identifique o Cartório de Registro</h3>
<p>O primeiro passo é descobrir em qual cartório o registro foi feito. Normalmente é o cartório do município onde a pessoa nasceu. Com o nome completo, data de nascimento e nome dos pais, é possível localizar o cartório responsável.</p>
<h3>2. Acesse o Serviço Online</h3>
<p>Plataformas especializadas como a E-Registro Brasil facilitam todo esse processo. Você preenche os dados solicitados, informa o endereço de entrega e realiza o pagamento online com segurança.</p>
<h3>3. Acompanhe o Andamento</h3>
<p>Após a solicitação, você receberá atualizações sobre o andamento do pedido por e-mail. O cartório emite a certidão e a envia para o endereço cadastrado.</p>

<h2>Prazo de Entrega</h2>
<p>O prazo para recebimento da segunda via varia conforme o cartório de origem e a localidade de entrega. Em média, o processo leva de <strong>5 a 15 dias úteis</strong> após a confirmação do pedido pelo cartório.</p>
<p>Para casos urgentes, alguns cartórios oferecem modalidades expressas, com prazo reduzido mediante taxa adicional.</p>

<h2>Dicas Importantes</h2>
<blockquote>
  <p>Guarde sempre uma cópia digitalizada dos seus documentos em nuvem. Em caso de perda do físico, o processo de obtenção da segunda via fica muito mais ágil.</p>
</blockquote>
<ul>
  <li>Não há limite de vezes para solicitar segunda via — você pode pedir quantas precisar</li>
  <li>A segunda via tem o mesmo valor legal que o documento original</li>
  <li>Certidões emitidas após 2010 podem ser verificadas pelo QR Code</li>
  <li>Menores de 18 anos devem ter a solicitação feita por um responsável legal</li>
</ul>
"""

ARTICLE_2_CONTENT = """
<h2>O que são Ônus Reais?</h2>
<p>Ônus reais são encargos, limitações ou restrições que recaem sobre um imóvel e acompanham a propriedade independentemente de quem seja o atual dono. Eles representam direitos de terceiros sobre o bem imóvel e precisam ser declarados e registrados na matrícula do imóvel.</p>
<p>Os principais tipos de ônus reais incluem: hipotecas, penhoras, usufruto, servidões, alienação fiduciária, anticrese e ações reais que podem afetar o imóvel.</p>

<h2>O que é a Certidão de Ônus Reais?</h2>
<p>A Certidão de Ônus Reais é um documento emitido pelo Cartório de Registro de Imóveis que comprova a existência ou não de qualquer ônus, encargo ou restrição registrado na matrícula de um imóvel. Ela apresenta o histórico completo das averbações e registros que constam na matrícula.</p>
<p>Trata-se de um dos documentos mais solicitados em transações imobiliárias, processos judiciais e financiamentos.</p>

<h2>Quando a Certidão de Ônus Reais é Necessária?</h2>
<ul>
  <li><strong>Compra e venda de imóvel:</strong> Para garantir que o bem está livre de dívidas e restrições antes de fechar negócio</li>
  <li><strong>Financiamento imobiliário:</strong> Os bancos exigem a certidão para liberar o crédito</li>
  <li><strong>Inventário e partilha:</strong> Para verificar a situação jurídica do imóvel do espólio</li>
  <li><strong>Processos judiciais:</strong> Como prova da situação registral do imóvel</li>
  <li><strong>Regularização de imóveis:</strong> Para verificar pendências antes de regularizar a situação</li>
</ul>

<h2>Como Obter a Certidão de Ônus Reais</h2>
<p>A certidão deve ser solicitada no Cartório de Registro de Imóveis da circunscrição onde o imóvel está localizado. Para identificar o cartório correto, é necessário ter o número da matrícula do imóvel ou o endereço completo.</p>
<p>Plataformas online especializadas, como a E-Registro Brasil, simplificam esse processo: basta informar os dados do imóvel e receber a certidão no endereço desejado, sem burocracia.</p>

<h2>Prazo de Validade</h2>
<p>A Certidão de Ônus Reais não possui prazo de validade legal fixo. Porém, na prática, a maioria das instituições financeiras e cartórios de notas aceita certidões emitidas com até <strong>30 dias de antecedência</strong>.</p>
<p>Para transações relevantes, recomenda-se sempre solicitar a certidão com data próxima à assinatura do contrato, evitando surpresas com registros recentes.</p>
"""

ARTICLE_3_CONTENT = """
<h2>O que é a Apostila de Haia?</h2>
<p>A Apostila de Haia é um certificado de autenticidade internacional criado pela Convenção da Haia de 1961, que simplifica o processo de validação de documentos entre os países signatários. Com a apostila, um documento público emitido em um país é reconhecido automaticamente em outro país membro, sem necessidade de legalização consular.</p>
<p>O Brasil aderiu à Convenção em 2016, e desde então os documentos apostilados em território brasileiro têm validade imediata em mais de 120 países.</p>

<h2>Quais Países Aceitam a Apostila de Haia?</h2>
<p>A Convenção conta atualmente com mais de 120 países signatários, incluindo:</p>
<ul>
  <li>Todos os países da União Europeia (Portugal, Itália, Espanha, França, Alemanha etc.)</li>
  <li>Estados Unidos, Canadá e México</li>
  <li>Argentina, Chile, Peru, Colômbia e demais países da América Latina</li>
  <li>Austrália, Nova Zelândia e Japão</li>
  <li>Israel, África do Sul e outros</li>
</ul>
<p>Para países não signatários da Convenção, ainda é necessário o processo de legalização consular.</p>

<h2>Quais Documentos Podem ser Apostilados?</h2>
<p>Podem ser apostilados documentos públicos ou autenticados por tabelião, como:</p>
<ul>
  <li>Certidões de nascimento, casamento e óbito</li>
  <li>Diplomas e históricos escolares autenticados</li>
  <li>Procurações públicas e escrituras</li>
  <li>Certidões criminais e de antecedentes</li>
  <li>Documentos judiciais e administrativos</li>
  <li>Traduções juramentadas autenticadas</li>
</ul>

<h2>Como Funciona o Processo de Apostilamento no Brasil</h2>
<p>No Brasil, o apostilamento é realizado pelos Tribunais de Justiça dos estados e pelo Superior Tribunal de Justiça (STJ), dependendo do tipo e origem do documento. O processo envolve:</p>
<h3>Passo 1: Verificação do Documento</h3>
<p>O documento deve ser original ou cópia autenticada em cartório. Documentos particulares precisam ser reconhecidos por tabelião antes de serem apostilados.</p>
<h3>Passo 2: Solicitação da Apostila</h3>
<p>A solicitação pode ser feita presencialmente nos cartórios habilitados ou por meio de plataformas online como a E-Registro Brasil, que cuidam de toda a logística junto ao Tribunal competente.</p>
<h3>Passo 3: Entrega</h3>
<p>A apostila é uma etiqueta ou carimbo aposto no próprio documento, acompanhado de certificado digital com QR code para verificação online.</p>

<h2>Prazo e Custo</h2>
<p>O prazo para apostilamento varia conforme o Tribunal e a modalidade. Em geral, o processo leva de <strong>3 a 10 dias úteis</strong>. O custo é composto pela taxa do Tribunal (fixada em tabela oficial) mais eventuais taxas de serviço da plataforma utilizada.</p>
"""

ARTICLE_4_CONTENT = """
<h2>O que é a Matrícula de Imóvel?</h2>
<p>A matrícula de imóvel é o registro oficial e individualizado de um imóvel no Cartório de Registro de Imóveis. Funciona como a "identidade" do imóvel: cada bem possui um número de matrícula único naquele cartório, que contém todo o histórico da propriedade desde sua criação.</p>
<p>Na matrícula constam: descrição do imóvel (área, localização, confrontações), histórico de proprietários, atos de transferência, gravames, penhoras, hipotecas e quaisquer outras averbações que afetem o bem.</p>

<h2>O que é a Certidão de Imóvel?</h2>
<p>A Certidão de Imóvel é um documento emitido pelo Cartório de Registro de Imóveis que reproduz, oficialmente, o conteúdo da matrícula. É a prova documental do que está registrado sobre aquele imóvel.</p>
<p>Enquanto a matrícula é o registro em si (mantido fisicamente no cartório), a certidão é a reprodução oficial desse registro, emitida quando solicitada por interessados.</p>

<h2>Tipos de Certidão de Imóvel</h2>
<ul>
  <li><strong>Certidão de Inteiro Teor:</strong> Reprodução completa de toda a matrícula, incluindo todos os atos desde a abertura</li>
  <li><strong>Certidão de Ônus Reais:</strong> Informa os encargos, restrições e gravames que recaem sobre o imóvel</li>
  <li><strong>Certidão de Propriedade:</strong> Confirma quem é o atual proprietário registrado do imóvel</li>
  <li><strong>Certidão Negativa de Ônus:</strong> Confirma que não há ônus ou restrições registrados</li>
  <li><strong>Certidão Vintenária:</strong> Apresenta os registros dos últimos 20 anos da matrícula</li>
</ul>

<h2>Qual é a Diferença Prática?</h2>
<p>A diferença fundamental é:</p>
<ul>
  <li><strong>Matrícula</strong> → É o registro em si, existente no cartório. Você não "tem" a matrícula em mãos normalmente.</li>
  <li><strong>Certidão</strong> → É o documento que você solicita ao cartório para comprovar o que consta na matrícula. Você a obtém fisicamente ou digitalmente.</li>
</ul>
<p>Em termos práticos: quando alguém pede "a certidão do imóvel", está pedindo que o cartório emita um documento certificando o conteúdo da matrícula naquele momento.</p>

<h2>Quando Solicitar a Certidão de Imóvel?</h2>
<p>A certidão de imóvel é indispensável em diversas situações:</p>
<ul>
  <li>Antes de comprar um imóvel (verificar proprietário real e existência de dívidas)</li>
  <li>Para financiamento bancário (bancos sempre exigem)</li>
  <li>Em processos de inventário e partilha de bens</li>
  <li>Para regularização de imóveis sem escritura</li>
  <li>Em ações judiciais envolvendo o imóvel</li>
  <li>Para calcular o ITBI (Imposto de Transmissão de Bens Imóveis)</li>
</ul>
<blockquote>
  <p>Sempre solicite a certidão de imóvel antes de assinar qualquer contrato de compra e venda. Isso protege você de surpresas como hipotecas, penhoras ou problemas na titularidade.</p>
</blockquote>
"""


class Command(BaseCommand):
    help = "Cria categorias e artigos iniciais para o blog (idempotente)"

    def handle(self, *args, **options):
        self.stdout.write("Criando categorias do blog...")
        category_map = {}
        for name, slug, description in CATEGORIES:
            cat, created = BlogCategory.objects.get_or_create(
                slug=slug,
                defaults={"name": name, "description": description},
            )
            if not created and not cat.description:
                cat.description = description
                cat.save(update_fields=["description"])
            category_map[slug] = cat
            status = "criada" if created else "já existe"
            self.stdout.write(f"  [{status}] {name}")

        author = User.objects.filter(is_superuser=True).first()
        if not author:
            self.stdout.write(self.style.WARNING(
                "Nenhum superusuário encontrado. Crie um via createsuperuser e rode o comando novamente."
            ))
            return

        self.stdout.write(f"\nAutor: {author.get_full_name() or author.username}")
        self.stdout.write("Criando artigos...")

        articles = [
            {
                "slug": "como-solicitar-segunda-via-certidao-nascimento-online",
                "title": "Como Solicitar Segunda Via de Certidão de Nascimento Online",
                "category_slug": "segunda-via",
                "excerpt": "Saiba como solicitar a segunda via da certidão de nascimento online de forma rápida e segura. Guia completo com passo a passo.",
                "content": ARTICLE_1_CONTENT,
                "tags": "certidão de nascimento, segunda via, registro civil, documentos",
                "meta_title": "Como Solicitar Segunda Via de Certidão de Nascimento Online — E-Registro Brasil",
                "meta_description": "Saiba como solicitar a segunda via da certidão de nascimento online de forma rápida e segura. Guia completo com passo a passo.",
                "is_featured": True,
            },
            {
                "slug": "certidao-de-onus-reais-o-que-e-para-que-serve",
                "title": "Certidão de Ônus Reais: O Que É e Para Que Serve",
                "category_slug": "certidoes-de-imoveis",
                "excerpt": "Entenda o que é a Certidão de Ônus Reais, quando ela é necessária e como solicitar junto ao Cartório de Registro de Imóveis.",
                "content": ARTICLE_2_CONTENT,
                "tags": "ônus reais, registro de imóveis, imóvel, gravames, hipoteca",
                "meta_title": "Certidão de Ônus Reais: O Que É e Para Que Serve — E-Registro Brasil",
                "meta_description": "Entenda o que é a Certidão de Ônus Reais, quando ela é necessária e como solicitar junto ao Cartório de Registro de Imóveis.",
                "is_featured": False,
            },
            {
                "slug": "apostila-de-haia-guia-completo",
                "title": "Apostila de Haia: Guia Completo para Validar Documentos no Exterior",
                "category_slug": "apostilamento",
                "excerpt": "Saiba o que é a Apostila de Haia, quais países aceitam, quais documentos podem ser apostilados e como funciona o processo no Brasil.",
                "content": ARTICLE_3_CONTENT,
                "tags": "apostila de haia, documentos internacionais, legalização, exterior",
                "meta_title": "Apostila de Haia: Guia Completo para Validar Documentos no Exterior — E-Registro Brasil",
                "meta_description": "Saiba o que é a Apostila de Haia, quais países aceitam, quais documentos podem ser apostilados e como funciona o processo no Brasil.",
                "is_featured": False,
            },
            {
                "slug": "matricula-de-imovel-e-certidao-de-imovel-diferenca",
                "title": "Matrícula de Imóvel e Certidão de Imóvel: Qual a Diferença?",
                "category_slug": "certidoes-de-imoveis",
                "excerpt": "Descubra as diferenças entre matrícula de imóvel e certidão de imóvel, quais são os tipos de certidão e quando você precisa de cada uma.",
                "content": ARTICLE_4_CONTENT,
                "tags": "matrícula de imóvel, certidão de imóvel, registro de imóveis, documentação",
                "meta_title": "Matrícula de Imóvel e Certidão de Imóvel: Qual a Diferença? — E-Registro Brasil",
                "meta_description": "Descubra as diferenças entre matrícula de imóvel e certidão de imóvel, quais são os tipos de certidão e quando você precisa de cada uma.",
                "is_featured": False,
            },
        ]

        now = timezone.now()
        for data in articles:
            category = category_map.get(data["category_slug"])
            post, created = Post.objects.get_or_create(
                slug=data["slug"],
                defaults={
                    "title": data["title"],
                    "author": author,
                    "category": category,
                    "excerpt": data["excerpt"],
                    "content": data["content"],
                    "tags": data["tags"],
                    "meta_title": data["meta_title"],
                    "meta_description": data["meta_description"],
                    "meta_keywords": data["tags"],
                    "is_featured": data["is_featured"],
                    "is_published": True,
                    "published_at": now,
                },
            )
            if not created:
                post.title = data["title"]
                post.category = category
                post.excerpt = data["excerpt"]
                post.content = data["content"]
                post.tags = data["tags"]
                post.meta_title = data["meta_title"]
                post.meta_description = data["meta_description"]
                post.meta_keywords = data["tags"]
                post.is_featured = data["is_featured"]
                post.is_published = True
                if not post.published_at:
                    post.published_at = now
                post.save()

            status = "criado" if created else "atualizado"
            self.stdout.write(f"  [{status}] {data['title'][:60]}")

        self.stdout.write(self.style.SUCCESS("\nBlog seed concluído com sucesso!"))
