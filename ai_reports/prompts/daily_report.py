"""
Prompt templates para geração de relatórios diários.
"""
import json


SYSTEM_PROMPT = """Você é um analista de produtividade especializado em sistemas de gestão de cartórios e registros legais.
Sua tarefa é analisar logs de atividade de usuários e gerar relatórios estruturados em JSON.
Responda APENAS com JSON válido, sem texto adicional, sem markdown, sem blocos de código."""


def build_user_prompt(usuario_nome: str, data: str, metricas: dict) -> str:
    return f"""Analise as atividades do usuário abaixo e gere um relatório executivo.

USUÁRIO: {usuario_nome}
DATA: {data}
MÉTRICAS:
{json.dumps(metricas, ensure_ascii=False, indent=2)}

Responda com um JSON com exatamente esta estrutura:
{{
  "resumo_executivo": "Parágrafo de 2-3 frases descrevendo a atuação do usuário no dia",
  "principais_acoes": ["ação 1", "ação 2", "ação 3"],
  "score_produtividade": 75.0,
  "padroes_incomuns": ["observação sobre anomalia se houver"],
  "possiveis_gargalos": ["gargalo identificado se houver"],
  "recomendacoes": ["recomendação 1", "recomendação 2"],
  "alertas": ["alerta crítico se houver"],
  "modulos_mais_usados": ["modulo1", "modulo2"]
}}

Regras para score_produtividade (0-100):
- 90-100: Altíssima produtividade, muitas ações concluídas com sucesso
- 70-89: Boa produtividade
- 50-69: Produtividade moderada
- 30-49: Abaixo do esperado
- 0-29: Baixa produtividade ou possível inatividade"""
