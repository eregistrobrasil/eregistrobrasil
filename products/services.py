"""
Service layer: preços por estado e criação em massa de ServiceStatePrice.
"""
from decimal import Decimal
from typing import Optional

from products.models import State, ServiceStatePrice, Product, PrecoImovelEstado, ESTADOS_BR

# ─────────────────────────────────────────────────────────────────────────────
# Tabela de preços: Certidão de Nascimento 2ª Via
# Fonte: regras de negócio definidas pela equipe comercial.
# Editável também via Django Admin → Preços por Estado.
# ─────────────────────────────────────────────────────────────────────────────
PRECOS_CERTIDAO_NASCIMENTO: dict[str, Decimal] = {
    "AC": Decimal("219.90"),
    "AL": Decimal("229.90"),
    "AP": Decimal("219.90"),
    "AM": Decimal("229.90"),
    "BA": Decimal("349.90"),
    "CE": Decimal("229.90"),
    "DF": Decimal("219.90"),
    "ES": Decimal("229.90"),
    "GO": Decimal("229.90"),
    "MA": Decimal("229.90"),
    "MT": Decimal("229.90"),
    "MS": Decimal("229.90"),
    "MG": Decimal("229.90"),
    "PA": Decimal("349.90"),
    "PB": Decimal("249.90"),
    "PR": Decimal("219.90"),
    "PE": Decimal("229.90"),
    "PI": Decimal("229.90"),
    "RN": Decimal("229.90"),
    "RS": Decimal("219.90"),
    "RJ": Decimal("349.90"),
    "RO": Decimal("219.90"),
    "RR": Decimal("199.90"),
    "SC": Decimal("219.90"),
    "SP": Decimal("217.90"),
    "SE": Decimal("229.90"),
    "TO": Decimal("219.90"),
}

# Mapeamento de siglas válidas para fácil validação
_CODIGOS_VALIDOS: frozenset[str] = frozenset(code for code, _ in ESTADOS_BR)


# ─────────────────────────────────────────────────────────────────────────────
# Tabela de preços: Certidão de Casamento 2ª Via
# ─────────────────────────────────────────────────────────────────────────────
PRECOS_CERTIDAO_CASAMENTO: dict[str, Decimal] = {
    "AC": Decimal("219.90"),
    "AL": Decimal("229.90"),
    "AP": Decimal("219.90"),
    "AM": Decimal("229.90"),
    "BA": Decimal("349.90"),
    "CE": Decimal("229.90"),
    "DF": Decimal("219.90"),
    "ES": Decimal("229.90"),
    "GO": Decimal("229.90"),
    "MA": Decimal("229.90"),
    "MT": Decimal("229.90"),
    "MS": Decimal("229.90"),
    "MG": Decimal("229.90"),
    "PA": Decimal("349.90"),
    "PB": Decimal("249.90"),
    "PR": Decimal("219.90"),
    "PE": Decimal("229.90"),
    "PI": Decimal("229.90"),
    "RJ": Decimal("349.90"),
    "RN": Decimal("229.90"),
    "RS": Decimal("219.90"),
    "RO": Decimal("219.90"),
    "RR": Decimal("199.90"),
    "SC": Decimal("219.90"),
    "SP": Decimal("217.90"),
    "SE": Decimal("229.90"),
    "TO": Decimal("219.90"),
}


def obter_preco_certidao_nascimento(estado: str) -> Optional[Decimal]:
    """
    Retorna o preço da Certidão de Nascimento 2ª Via para o estado informado.
    - Valida o estado contra a lista oficial de UFs.
    - Retorna None se o estado não tiver preço específico configurado,
      sinalizando que deve ser usado o preço base do produto.
    """
    code = (estado or "").strip().upper()
    if code not in _CODIGOS_VALIDOS:
        return None
    return PRECOS_CERTIDAO_NASCIMENTO.get(code)


def obter_preco_certidao_casamento(estado: str) -> Optional[Decimal]:
    """
    Retorna o preço da Certidão de Casamento 2ª Via para o estado informado.
    Retorna None se o estado for inválido ou não tiver preço configurado.
    """
    code = (estado or "").strip().upper()
    if code not in _CODIGOS_VALIDOS:
        return None
    return PRECOS_CERTIDAO_CASAMENTO.get(code)


# ─────────────────────────────────────────────────────────────────────────────
# Tabela de preços: Certidão de Óbito 2ª Via
# ─────────────────────────────────────────────────────────────────────────────
PRECOS_CERTIDAO_OBITO: dict[str, Decimal] = {
    "AC": Decimal("219.90"),
    "AL": Decimal("229.90"),
    "AP": Decimal("219.90"),
    "AM": Decimal("229.90"),
    "BA": Decimal("349.90"),
    "CE": Decimal("229.90"),
    "DF": Decimal("219.90"),
    "ES": Decimal("229.90"),
    "GO": Decimal("229.90"),
    "MA": Decimal("229.90"),
    "MT": Decimal("229.90"),
    "MS": Decimal("229.90"),
    "MG": Decimal("229.90"),
    "PA": Decimal("349.90"),
    "PB": Decimal("249.90"),
    "PR": Decimal("219.90"),
    "PE": Decimal("229.90"),
    "PI": Decimal("229.90"),
    "RJ": Decimal("349.90"),
    "RN": Decimal("229.90"),
    "RS": Decimal("219.90"),
    "RO": Decimal("219.90"),
    "RR": Decimal("199.90"),
    "SC": Decimal("219.90"),
    "SP": Decimal("217.90"),
    "SE": Decimal("229.90"),
    "TO": Decimal("219.90"),
}


def obter_preco_certidao_obito(estado: str) -> Optional[Decimal]:
    """
    Retorna o preço da Certidão de Óbito 2ª Via para o estado informado.
    Retorna None se o estado for inválido ou não tiver preço configurado.
    """
    code = (estado or "").strip().upper()
    if code not in _CODIGOS_VALIDOS:
        return None
    return PRECOS_CERTIDAO_OBITO.get(code)


# ─────────────────────────────────────────────────────────────────────────────
# Tabela de preços: Certidão de Interdição
# ─────────────────────────────────────────────────────────────────────────────
PRECOS_CERTIDAO_INTERDICAO: dict[str, Decimal] = {
    "AC": Decimal("219.90"),
    "AL": Decimal("219.90"),
    "AP": Decimal("219.90"),
    "AM": Decimal("219.90"),
    "BA": Decimal("219.90"),
    "CE": Decimal("219.90"),
    "DF": Decimal("219.90"),
    "ES": Decimal("219.90"),
    "GO": Decimal("219.90"),
    "MA": Decimal("219.90"),
    "MT": Decimal("219.90"),
    "MS": Decimal("239.90"),
    "MG": Decimal("219.90"),
    "PA": Decimal("249.90"),
    "PB": Decimal("219.90"),
    "PR": Decimal("219.90"),
    "PE": Decimal("219.90"),
    "PI": Decimal("219.90"),
    "RJ": Decimal("359.90"),
    "RN": Decimal("219.90"),
    "RS": Decimal("219.90"),
    "RO": Decimal("219.90"),
    "RR": Decimal("219.90"),
    "SC": Decimal("219.90"),
    "SP": Decimal("219.90"),
    "SE": Decimal("219.90"),
    "TO": Decimal("219.90"),
}


def obter_preco_certidao_interdicao(estado: str) -> Optional[Decimal]:
    """
    Retorna o preço da Certidão de Interdição para o estado informado.
    Retorna None se o estado for inválido ou não tiver preço configurado.
    """
    code = (estado or "").strip().upper()
    if code not in _CODIGOS_VALIDOS:
        return None
    return PRECOS_CERTIDAO_INTERDICAO.get(code)


# ─────────────────────────────────────────────────────────────────────────────
# Tabela de preços: Certidão de Procuração
# ─────────────────────────────────────────────────────────────────────────────
PRECOS_CERTIDAO_PROCURACAO: dict[str, Decimal] = {
    "AC": Decimal("219.90"),
    "AL": Decimal("219.90"),
    "AP": Decimal("219.90"),
    "AM": Decimal("219.90"),
    "BA": Decimal("219.90"),
    "CE": Decimal("219.90"),
    "DF": Decimal("149.90"),
    "ES": Decimal("219.90"),
    "GO": Decimal("219.90"),
    "MA": Decimal("219.90"),
    "MT": Decimal("209.90"),
    "MS": Decimal("219.90"),
    "MG": Decimal("219.90"),
    "PA": Decimal("209.90"),
    "PB": Decimal("219.90"),
    "PR": Decimal("209.90"),
    "PE": Decimal("219.90"),
    "PI": Decimal("219.90"),
    "RJ": Decimal("359.90"),
    "RN": Decimal("219.90"),
    "RS": Decimal("209.90"),
    "RO": Decimal("219.90"),
    "RR": Decimal("219.90"),
    "SC": Decimal("219.90"),
    "SP": Decimal("129.90"),
    "SE": Decimal("219.90"),
    "TO": Decimal("259.90"),
}


def obter_preco_certidao_procuracao(estado: str) -> Optional[Decimal]:
    """
    Retorna o preço da Certidão de Procuração para o estado informado.
    - Valida a sigla contra a lista oficial de UFs brasileiras.
    - Retorna None se o estado for inválido ou não tiver preço configurado,
      sinalizando fallback para o preço base do produto.
    """
    code = (estado or "").strip().upper()
    if code not in _CODIGOS_VALIDOS:
        return None
    return PRECOS_CERTIDAO_PROCURACAO.get(code)


def obter_preco_por_estado(product: "Product", estado: str) -> Optional[Decimal]:
    """
    Consulta o banco de dados para obter o preço vigente de *qualquer* produto
    para um estado específico.
    Retorna None se não houver registro ativo, indicando fallback para o preço base.
    Esta é a função usada nas views — nunca confia no preço vindo do frontend.
    """
    code = (estado or "").strip().upper()
    if not code or code not in _CODIGOS_VALIDOS:
        return None
    try:
        ssp = ServiceStatePrice.objects.select_related("state").get(
            service=product, state__code=code, is_active=True
        )
        return ssp.display_price
    except ServiceStatePrice.DoesNotExist:
        return None


def get_state_prices_dict(product: "Product") -> dict[str, str]:
    """
    Retorna um dicionário {sigla: preco_string} para todos os estados ativos
    de um produto. Usado no template para evitar chamadas AJAX por estado.
    """
    return {
        ssp.state.code: str(ssp.display_price)
        for ssp in product.state_prices.filter(is_active=True).select_related("state")
    }


# ─────────────────────────────────────────────────────────────────────────────
# Utilitários de manutenção de dados
# ─────────────────────────────────────────────────────────────────────────────

def criar_precos_para_todos_estados(product):
    """
    Cria registros ServiceStatePrice para todos os estados que ainda não existem.
    Usa o price atual do produto como valor base.
    """
    estados = State.objects.all()
    existentes = set(
        ServiceStatePrice.objects
        .filter(service=product)
        .values_list('state_id', flat=True)
    )
    novos = [
        ServiceStatePrice(service=product, state=estado, price=product.price)
        for estado in estados
        if estado.pk not in existentes
    ]
    if novos:
        ServiceStatePrice.objects.bulk_create(novos, ignore_conflicts=True)


def sincronizar_preco_base(product, novo_preco):
    """
    Ao alterar o preço base do produto, atualiza todos os estados que ainda tinham
    o preço igual ao antigo (ou seja, não foram customizados).
    Retorna a quantidade de estados atualizados.
    """
    updated = (
        ServiceStatePrice.objects
        .filter(service=product, price=product.price)
        .update(price=novo_preco)
    )
    return updated


# ─────────────────────────────────────────────────────────────────────────────
# Tabela de preços: Certidão de Imóvel (por tipo)
# ─────────────────────────────────────────────────────────────────────────────

def obter_preco_imovel(tipo_certidao: str, estado: str) -> Optional[Decimal]:
    """
    Retorna o preço da Certidão de Imóvel para o tipo e estado informados.
    Consulta PrecoImovelEstado — nunca confia em dados vindos do frontend.
    Retorna None se não houver preço ativo configurado.
    """
    code = (estado or "").strip().upper()
    if not code or code not in _CODIGOS_VALIDOS:
        return None
    tipo = (tipo_certidao or "").strip().lower()
    if not tipo:
        return None
    try:
        obj = PrecoImovelEstado.objects.select_related("state").get(
            tipo_certidao=tipo, state__code=code, is_active=True
        )
        return obj.price
    except PrecoImovelEstado.DoesNotExist:
        return None


def get_imovel_prices_dict(tipo_certidao: str) -> dict[str, str]:
    """
    Retorna um dicionário {sigla_estado: preco_string} para todos os estados
    ativos de um tipo de certidão de imóvel.
    Usado no template para embutir o JSON e evitar chamadas AJAX por estado.
    """
    tipo = (tipo_certidao or "").strip().lower()
    return {
        obj.state.code: str(obj.price)
        for obj in (
            PrecoImovelEstado.objects
            .filter(tipo_certidao=tipo, is_active=True)
            .select_related("state")
        )
    }
