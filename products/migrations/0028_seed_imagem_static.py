# Data migration — popula imagem_static para todos os serviços do sistema.
# Idempotente: só atualiza registros onde o campo ainda está vazio.
# Adicione novos mapeamentos neste dicionário conforme surgirem novos serviços.

from django.db import migrations

# slug → caminho relativo dentro de static/
IMAGEM_POR_SLUG = {
    # ── Registro Civil ────────────────────────────────────────────────────────
    "certidao-de-nascimento-2a-via":         "img/servicos/certidao-nascimento.webp",
    "certidao-de-casamento-2a-via":          "img/servicos/certidao-casamento.webp",
    "certidao-de-obito-2a-via":              "img/servicos/certidao-obito.webp",
    "certidao-de-interdicao":                "img/servicos/certidao-interdicao.webp",

    # ── Tabelionato de Notas ──────────────────────────────────────────────────
    "certidao-de-procuracao":                "img/servicos/procuracao.webp",
    "certidao-de-escritura":                 "img/servicos/escritura.webp",
    "certidao-de-escritura-de-uniao-estavel":"img/servicos/uniao-estavel.webp",
    "certidao-de-escritura-de-ata-notarial": "img/servicos/escritura.webp",
    "certidao-de-escritura-de-compra-e-venda":"img/servicos/escritura-compra-venda.webp",
    "certidao-de-escritura-de-divorcio":     "img/servicos/escritura-divorcio.webp",
    "certidao-de-escritura-de-doacao":       "img/servicos/escritura.webp",
    "certidao-de-escritura-de-emancipacao":  "img/servicos/escritura.webp",
    "certidao-de-escritura-de-hipoteca":     "img/servicos/escritura.webp",
    "certidao-de-escritura-de-inventario":   "img/servicos/escritura-inventario.webp",
    "certidao-de-escritura-de-pacto-antenupcial": "img/servicos/escritura.webp",
    "certidao-de-escritura-de-permuta":      "img/servicos/escritura.webp",
    "certidao-de-escritura-de-testamento":   "img/servicos/escritura-testamento.webp",

    # ── Registro de Imóveis ───────────────────────────────────────────────────
    "certidao-de-imovel":                    "img/servicos/certidao-imovel.webp",
    "certidao-de-penhor-de-safra":           "img/servicos/certidao-imovel.webp",
    "pacote-de-certidoes-compra-e-venda-de-imovel": "img/servicos/pacote-certidoes-imovel.webp",
    "certidao-de-matricula-atualizada":      "img/servicos/certidao-matricula.webp",
    "certidao-de-onus-reais":               "img/servicos/certidao-imovel.webp",
    "certidao-negativa-de-alienacao-fiduciaria": "img/servicos/certidao-imovel.webp",
    "pesquisa-de-bens":                      "img/servicos/pesquisa-bens.webp",

    # ── Tabelionato de Protestos ──────────────────────────────────────────────
    "certidao-de-protesto":                  "img/servicos/certidao-protesto.webp",
    "busca-de-protesto":                     "img/servicos/certidao-protesto.webp",
    "pesquisa-de-protesto-nacional":         "img/servicos/certidao-protesto.webp",

    # ── Federais e Estaduais ──────────────────────────────────────────────────
    "cnd-federal-receita-federal":           "img/servicos/certidao-federal.webp",
    "certidao-fgts-inss":                   "img/servicos/certidao-federal.webp",
    "cnd-estadual-sefaz":                   "img/servicos/certidao-federal.webp",
    "certidao-negativa-municipio":           "img/servicos/certidao-federal.webp",
    "certidao-regularidade-crea":            "img/servicos/certidao-federal.webp",
    "certidao-antecedentes-criminais":       "img/servicos/antecedentes-criminais.webp",
    "tse-certidao-de-quitacao-eleitoral":    "img/servicos/certidao-federal.webp",
    "cnd-itr-receita-federal":               "img/servicos/certidao-federal.webp",
    "cnj-improbidade-administrativa-e-inelegibilidade": "img/servicos/certidao-federal.webp",

    # ── Busca em Cartórios ────────────────────────────────────────────────────
    "busca-em-cartorios-registro-civil":     "img/servicos/busca-registro.webp",
    "busca-em-tabelionatos-notas":           "img/servicos/busca-registro.webp",
    "certidao-negativa-de-testamento":       "img/servicos/certidao-testamento.webp",

    # ── Apostilamento ─────────────────────────────────────────────────────────
    "apostila-de-haia":                      "img/servicos/apostila-haia.webp",
    "traducao-juramentada":                  "img/servicos/traducao-juramentada.webp",
}


def seed_imagens(apps, schema_editor):
    Product = apps.get_model("products", "Product")
    for slug, caminho in IMAGEM_POR_SLUG.items():
        Product.objects.filter(slug=slug, imagem_static="").update(imagem_static=caminho)


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("products", "0027_product_imagem_static"),
    ]

    operations = [
        migrations.RunPython(seed_imagens, noop),
    ]
