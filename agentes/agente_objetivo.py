"""AGENTE C — Lógico + objetivo, com planejamento por BFS (Aulas 3, 4 e 6).  [0,6 ponto]

Reaproveita o Agente B para saber ONDE é seguro e usa busca em largura (BFS)
para planejar COMO chegar lá. Máquina de estados sugerida (slide 10):

  EXPLORAR  → BFS até a casa segura não visitada mais próxima
  AGARRAR   → quando houver brilho na casa atual
  VOLTAR    → BFS até (1,1) passando apenas por casas provadas seguras
  SAIR      → chegou em (1,1) com o ouro

Decisão aberta — o dilema do risco: sem casa segura e sem ouro, o agente deve
sair, atirar a flecha (−10) ou arriscar uma casa incerta? Decidam por utilidade
esperada e justifiquem no relatório.

A função acoes_para_vizinho() (em wumpus) transforma cada passo do caminho da BFS
em giros + AVANCAR. A BFS em si é implementação do grupo.
"""

from collections import deque  # noqa: F401

from wumpus import Acao, Percepcao, acoes_para_vizinho, vizinhos  # noqa: F401

from agentes.agente_logico import AgenteLogico


class AgenteObjetivo(AgenteLogico):
    nome = "C · Lógico + BFS"

    def __init__(self):
        super().__init__()
        self.fase = "explorar"
        self.plano = []  # fila de ações já planejadas

    def bfs(self, origem, destinos, permitidas):
        """Menor caminho (lista de casas) de `origem` até alguma casa de `destinos`,
        andando só por casas em `permitidas`. Devolve None se não houver caminho."""
        # TODO (grupo)
        raise NotImplementedError

    def agir(self, percepcao: Percepcao) -> Acao:
        # TODO (grupo): TELL/ASK como no Agente B, depois fase → plano → ação
        raise NotImplementedError("Agente C ainda não implementado")

    def depurar(self) -> str:
        return f"Fase: {self.fase} | Plano: {[str(a) for a in self.plano]}"
