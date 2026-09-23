"""AGENTE A — Reativo simples (Aula 4, tipo 1).                      [0,3 ponto]

Regras condição → ação, SEM MEMÓRIA: a decisão depende apenas da percepção atual.
Não guarde nada em self entre chamadas (nada de casas visitadas, "já peguei o ouro"
etc.). É o baseline do experimento e existe para mostrar o limite dos reativos.

Perguntas para guiar o projeto das regras:
  - O que fazer quando há brilho? E quando há brisa ou fedor?
  - Sem memória, como o agente sabe que já está com o ouro? E como volta a (1,1)?
  - O que fazer depois de um baque?
  - Qual regra evita que ele fique girando para sempre?

No relatório, explique quais mundos derrotam este agente e por quê.
"""

from wumpus import Acao, Agente, Percepcao


class AgenteReativo(Agente):
    nome = "A · Reativo"

    def agir(self, percepcao: Percepcao) -> Acao:
        # TODO (grupo): implemente as regras condição → ação.
        raise NotImplementedError("Agente A ainda não implementado")
