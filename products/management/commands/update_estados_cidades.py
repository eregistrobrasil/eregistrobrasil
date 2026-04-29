"""
Management command: update_estados_cidades
==========================================
Consome a API oficial do IBGE para obter todos os municípios do Brasil,
agrupa por UF, ordena alfabeticamente e salva em:

    static/js/estados_cidades.json

Uso:
    python manage.py update_estados_cidades
    python manage.py update_estados_cidades --force   # ignora cache
    python manage.py update_estados_cidades --output caminho/customizado.json
"""

import gzip
import json
import logging
import os
import time
from pathlib import Path
from typing import Optional

import urllib.request
import urllib.error

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

logger = logging.getLogger(__name__)

# ─── Configurações ────────────────────────────────────────────────────────────

IBGE_API_URL = "https://servicodados.ibge.gov.br/api/v1/localidades/municipios"

# Localização padrão do arquivo de saída (relativo à BASE_DIR do projeto)
DEFAULT_OUTPUT_RELATIVE = os.path.join("static", "js", "estados_cidades.json")

# Tempo de validade do cache local em segundos (padrão: 7 dias)
CACHE_TTL_SECONDS = 7 * 24 * 60 * 60

# Timeout da requisição HTTP em segundos
HTTP_TIMEOUT = 30


# ─── Funções utilitárias ───────────────────────────────────────────────────────


def fetch_municipios_ibge(timeout: int = HTTP_TIMEOUT) -> list[dict]:
    """
    Faz requisição à API do IBGE e retorna a lista bruta de municípios.

    Retorna:
        Lista de dicts com os dados de cada município.

    Lança:
        CommandError em caso de falha na requisição ou dados inválidos.
    """
    logger.info("Consultando API do IBGE: %s", IBGE_API_URL)
    try:
        req = urllib.request.Request(
            IBGE_API_URL,
            headers={
                "Accept": "application/json",
                "Accept-Encoding": "gzip, deflate",
                "User-Agent": "e-registro-brasil/1.0",
            },
        )
        with urllib.request.urlopen(req, timeout=timeout) as response:
            raw = response.read()
            # Descomprime gzip se necessário
            if raw[:2] == b'\x1f\x8b':
                raw = gzip.decompress(raw)
            data = json.loads(raw.decode("utf-8"))
    except urllib.error.HTTPError as exc:
        raise CommandError(f"Erro HTTP {exc.code} ao acessar a API do IBGE: {exc.reason}") from exc
    except urllib.error.URLError as exc:
        raise CommandError(f"Falha de conexão com a API do IBGE: {exc.reason}") from exc
    except json.JSONDecodeError as exc:
        raise CommandError(f"Resposta da API do IBGE não é um JSON válido: {exc}") from exc

    if not isinstance(data, list) or len(data) == 0:
        raise CommandError("API do IBGE retornou dados inesperados (lista vazia ou tipo incorreto).")

    logger.info("Recebidos %d municípios da API do IBGE.", len(data))
    return data


def validate_municipio(municipio: dict) -> bool:
    """
    Valida a estrutura de um município retornado pela API do IBGE.

    Campos esperados:
        - nome (str)
        - microrregiao.mesorregiao.UF.sigla (str, 2 chars)
        - microrregiao.mesorregiao.UF.nome (str)

    Retorna True se válido, False caso contrário.
    """
    try:
        nome = municipio.get("nome", "").strip()
        uf_sigla = (
            municipio["microrregiao"]["mesorregiao"]["UF"]["sigla"]
            .strip()
            .upper()
        )
        uf_nome = municipio["microrregiao"]["mesorregiao"]["UF"]["nome"].strip()
        return bool(nome) and len(uf_sigla) == 2 and bool(uf_nome)
    except (KeyError, AttributeError, TypeError):
        return False


def build_estados_cidades(municipios_raw: list[dict]) -> dict[str, dict]:
    """
    Transforma a lista bruta da API no formato estruturado:

        {
            "UF": {
                "nome": "Nome do Estado",
                "cidades": ["Cidade A", "Cidade B", ...]
            }
        }

    Garantias:
        - Cidades ordenadas alfabeticamente
        - Sem duplicidades
        - UFs ordenadas pela sigla
    """
    estados: dict[str, dict] = {}
    skipped = 0

    for municipio in municipios_raw:
        if not validate_municipio(municipio):
            logger.warning("Município inválido ignorado: %s", municipio)
            skipped += 1
            continue

        uf_sigla = municipio["microrregiao"]["mesorregiao"]["UF"]["sigla"].strip().upper()
        uf_nome = municipio["microrregiao"]["mesorregiao"]["UF"]["nome"].strip()
        cidade = municipio["nome"].strip()

        if uf_sigla not in estados:
            estados[uf_sigla] = {"nome": uf_nome, "cidades": set()}

        estados[uf_sigla]["cidades"].add(cidade)

    if skipped:
        logger.warning("%d municípios ignorados por dados inválidos.", skipped)

    # Converte sets para listas ordenadas e ordena por sigla
    return {
        sigla: {
            "nome": dados["nome"],
            "cidades": sorted(dados["cidades"]),
        }
        for sigla, dados in sorted(estados.items())
    }


def is_cache_valid(filepath: Path, ttl_seconds: int = CACHE_TTL_SECONDS) -> bool:
    """
    Verifica se o arquivo de cache existe e ainda está dentro do TTL.
    """
    if not filepath.exists():
        return False
    age = time.time() - filepath.stat().st_mtime
    return age < ttl_seconds


def save_json(data: dict, filepath: Path) -> None:
    """
    Salva o dicionário como JSON UTF-8 formatado no caminho especificado.
    Cria os diretórios intermediários se necessário.
    """
    filepath.parent.mkdir(parents=True, exist_ok=True)
    with filepath.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    logger.info("Arquivo salvo em: %s", filepath)


def load_json(filepath: Path) -> Optional[dict]:
    """
    Carrega e retorna o JSON do arquivo indicado.
    Retorna None se o arquivo não existir ou for inválido.
    """
    if not filepath.exists():
        return None
    try:
        with filepath.open("r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError) as exc:
        logger.warning("Falha ao carregar cache '%s': %s", filepath, exc)
        return None


def update_estados_cidades(
    output_path: Optional[Path] = None,
    force: bool = False,
    ttl_seconds: int = CACHE_TTL_SECONDS,
) -> dict[str, dict]:
    """
    Função principal reutilizável (pode ser importada em outros módulos).

    Fluxo:
        1. Se cache válido e não forçado → retorna dados do cache.
        2. Caso contrário → busca na API, valida, estrutura e salva.

    Args:
        output_path: Caminho para o JSON de saída. Se None, usa o padrão do projeto.
        force:       Ignora o cache e força nova busca na API.
        ttl_seconds: Tempo de validade do cache em segundos.

    Retorna:
        Dicionário estruturado { "UF": { "nome": ..., "cidades": [...] } }
    """
    if output_path is None:
        base_dir = Path(settings.BASE_DIR) if hasattr(settings, "BASE_DIR") else Path.cwd()
        output_path = base_dir / DEFAULT_OUTPUT_RELATIVE

    # Usa cache local se ainda válido
    if not force and is_cache_valid(output_path, ttl_seconds):
        logger.info("Cache válido encontrado. Usando '%s' (use --force para atualizar).", output_path)
        cached = load_json(output_path)
        if cached is not None:
            return cached
        logger.warning("Cache inválido, buscando dados na API.")

    # Busca dados frescos na API
    municipios_raw = fetch_municipios_ibge()
    estados_cidades = build_estados_cidades(municipios_raw)

    # Salva
    save_json(estados_cidades, output_path)

    total_cidades = sum(len(v["cidades"]) for v in estados_cidades.values())
    logger.info(
        "Concluído: %d estados, %d cidades únicas.",
        len(estados_cidades),
        total_cidades,
    )

    return estados_cidades


# ─── Management Command ────────────────────────────────────────────────────────


class Command(BaseCommand):
    help = (
        "Atualiza o arquivo estados_cidades.json a partir da API oficial do IBGE. "
        "Usa cache local para evitar chamadas desnecessárias à API."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--force",
            action="store_true",
            default=False,
            help="Ignora o cache local e força nova consulta à API do IBGE.",
        )
        parser.add_argument(
            "--output",
            type=str,
            default=None,
            help=(
                "Caminho customizado para o arquivo de saída. "
                f"Padrão: {DEFAULT_OUTPUT_RELATIVE}"
            ),
        )
        parser.add_argument(
            "--ttl",
            type=int,
            default=CACHE_TTL_SECONDS,
            help=f"Validade do cache em segundos (padrão: {CACHE_TTL_SECONDS}).",
        )

    def handle(self, *args, **options):
        output_path = Path(options["output"]) if options["output"] else None
        force = options["force"]
        ttl = options["ttl"]

        self.stdout.write("Iniciando atualização de estados e cidades...")

        try:
            dados = update_estados_cidades(
                output_path=output_path,
                force=force,
                ttl_seconds=ttl,
            )
        except CommandError as exc:
            raise
        except Exception as exc:
            raise CommandError(f"Erro inesperado: {exc}") from exc

        total_estados = len(dados)
        total_cidades = sum(len(v["cidades"]) for v in dados.values())

        self.stdout.write(
            self.style.SUCCESS(
                f"Concluído com sucesso: {total_estados} estados, {total_cidades} cidades únicas."
            )
        )

        # Resumo por estado
        self.stdout.write("\nResumo por estado:")
        for sigla, info in sorted(dados.items()):
            self.stdout.write(
                f"  {sigla} - {info['nome']}: {len(info['cidades'])} cidades"
            )
