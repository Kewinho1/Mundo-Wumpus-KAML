"""Agentes do grupo.

O REGISTRO define os atalhos aceitos por experimento.py e jogar.py:
    python experimento.py A B C
Para testar variações, acrescente entradas aqui (ex.: "B2": "agentes.agente_logico_v2:AgenteLogicoV2").
"""

REGISTRO = {
    "aleatorio": "agentes.agente_aleatorio:AgenteAleatorio",
    "A": "agentes.agente_reativo:AgenteReativo",
    "B": "agentes.agente_logico:AgenteLogico",
    "C": "agentes.agente_objetivo:AgenteObjetivo",
    # "D": "agentes.agente_llm:AgenteLLM",   # bônus
}
