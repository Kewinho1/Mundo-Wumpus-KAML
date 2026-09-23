"""Agente de EXEMPLO (fornecido pelo professor) — não faz parte da nota.

Mostra o contrato mínimo: herdar de Agente, definir `nome` e implementar agir().
Escolhe ações ao acaso, com duas regrinhas óbvias. Serve de piso para comparação:
qualquer um dos seus agentes deve ser melhor do que ele.
"""

import random

from wumpus import Acao, Agente, Percepcao


class AgenteAleatorio(Agente):
    nome = "Aleatório (exemplo)"

    def __init__(self):
        super().__init__()
        # Semente fixa: o agente se comporta igual em execuções repetidas.
        self.rng = random.Random(42)

    def agir(self, percepcao: Percepcao) -> Acao:
        if percepcao.brilho:
            return Acao.AGARRAR
        return self.rng.choice([Acao.AVANCAR, Acao.AVANCAR, Acao.VIRAR_ESQUERDA,
                                Acao.VIRAR_DIREITA, Acao.SAIR])
