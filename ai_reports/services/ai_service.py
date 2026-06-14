"""
Integração com a API Anthropic Claude para geração de relatórios.
A chave de API é lida exclusivamente de variáveis de ambiente.
"""
import json
import logging
from datetime import date
from collections import Counter

from django.conf import settings

logger = logging.getLogger(__name__)


def _calcular_metricas(usuario, atividades) -> dict:
    """Agrega as atividades do dia em métricas para o prompt."""
    acoes = Counter(a.acao for a in atividades)
    modulos = Counter(a.modulo for a in atividades)
    status = Counter(a.status for a in atividades)
    tempos = [a.tempo_execucao for a in atividades if a.tempo_execucao]
    tempo_medio = round(sum(tempos) / len(tempos), 2) if tempos else None

    # Estimativa de tempo ativo: soma dos tempos de execução em minutos
    tempo_total_ms = sum(tempos) if tempos else 0
    tempo_ativo_min = round(tempo_total_ms / 60000, 1)

    erros = [a for a in atividades if a.status in ('erro', 'negado')]
    falhas_login = acoes.get('falha_login', 0)

    return {
        'total_acoes': atividades.count(),
        'acoes_por_tipo': dict(acoes.most_common()),
        'modulos_acessados': dict(modulos.most_common()),
        'status_resumo': dict(status),
        'tempo_medio_resposta_ms': tempo_medio,
        'tempo_ativo_estimado_min': tempo_ativo_min,
        'total_erros': len(erros),
        'falhas_login': falhas_login,
        'urls_mais_acessadas': _top_urls(atividades),
    }


def _top_urls(atividades, n=5) -> list:
    counter = Counter(a.url for a in atividades if a.url)
    return [{'url': url, 'acessos': cnt} for url, cnt in counter.most_common(n)]


def _chamar_api_ia(usuario_nome: str, data_str: str, metricas: dict) -> dict:
    """
    Envia o prompt para a API Anthropic e retorna o JSON parseado.
    Requer ANTHROPIC_API_KEY no ambiente.
    """
    api_key = getattr(settings, 'ANTHROPIC_API_KEY', '')
    if not api_key:
        logger.warning('ANTHROPIC_API_KEY não configurada — relatório sem análise de IA.')
        return _relatorio_fallback(metricas)

    from ai_reports.prompts.daily_report import SYSTEM_PROMPT, build_user_prompt

    try:
        import anthropic

        client = anthropic.Anthropic(api_key=api_key)
        model = getattr(settings, 'AI_MODEL', 'claude-haiku-4-5-20251001')

        mensagem = client.messages.create(
            model=model,
            max_tokens=1024,
            system=SYSTEM_PROMPT,
            messages=[
                {'role': 'user', 'content': build_user_prompt(usuario_nome, data_str, metricas)},
            ],
        )

        conteudo = mensagem.content[0].text.strip()
        return json.loads(conteudo)

    except ImportError:
        logger.error('Pacote anthropic não instalado. Execute: pip install anthropic')
        return _relatorio_fallback(metricas)
    except json.JSONDecodeError as exc:
        logger.error('Resposta da IA não é JSON válido: %s', exc)
        return _relatorio_fallback(metricas)
    except Exception as exc:
        logger.exception('Erro ao chamar API de IA: %s', exc)
        return _relatorio_fallback(metricas)


def _relatorio_fallback(metricas: dict) -> dict:
    """Relatório gerado localmente quando a IA não está disponível."""
    total = metricas.get('total_acoes', 0)
    erros = metricas.get('total_erros', 0)
    score = max(0.0, min(100.0, 60.0 - (erros * 5) + min(total, 20) * 2))
    modulos = list(metricas.get('modulos_acessados', {}).keys())

    return {
        'resumo_executivo': f'Usuário realizou {total} ações durante o dia com {erros} erro(s).',
        'principais_acoes': list(metricas.get('acoes_por_tipo', {}).keys())[:3],
        'score_produtividade': round(score, 1),
        'padroes_incomuns': [f'{erros} erro(s) detectado(s)'] if erros > 3 else [],
        'possiveis_gargalos': [],
        'recomendacoes': ['Analisar os erros do dia para melhorar a eficiência.'] if erros else [],
        'alertas': [f'Múltiplas falhas de login detectadas: {metricas.get("falhas_login", 0)}']
                   if metricas.get('falhas_login', 0) >= 3 else [],
        'modulos_mais_usados': modulos[:3],
    }


def gerar_relatorio_usuario(usuario, data_ref: date) -> dict:
    """Gera e persiste o relatório diário de um usuário."""
    from audit.models import UserActivity
    from ai_reports.models import DailyUserReport

    atividades = UserActivity.objects.filter(
        usuario=usuario,
        data_hora__date=data_ref,
    )

    metricas = _calcular_metricas(usuario, atividades)
    usuario_nome = usuario.get_full_name() or usuario.username
    data_str = data_ref.strftime('%d/%m/%Y')

    analise = _chamar_api_ia(usuario_nome, data_str, metricas)

    relatorio, _ = DailyUserReport.objects.update_or_create(
        usuario=usuario,
        data=data_ref,
        defaults={
            'resumo': analise.get('resumo_executivo', ''),
            'indicadores': metricas,
            'recomendacoes': analise.get('recomendacoes', []),
            'alertas': analise.get('alertas', []),
            'score_produtividade': float(analise.get('score_produtividade', 0)),
            'total_acoes': metricas.get('total_acoes', 0),
            'modulos_acessados': list(metricas.get('modulos_acessados', {}).keys()),
        },
    )
    return relatorio
