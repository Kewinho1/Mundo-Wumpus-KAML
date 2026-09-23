"""AGENTE A — Reativo simples (Aula 4, tipo 1).                      [0,3 ponto]

Regras condição → ação, SEM MEMÓRIA: a decisão depende apenas da percepção atual.
Não guarde nada em self entre chamadas (nada de casas visitadas, "já peguei o ouro"
etc.). É o baseline do experimento e existe para mostrar o limite dos reativos.

Regras (avaliadas em ordem, a primeira que casar decide):
  R1  brilho                                  → AGARRAR
  R2  em (1,1) e (brisa ou fedor)             → SAIR   (a entrada já é perigosa)
  R3  em (1,1), 15% das vezes                 → SAIR   (é o único jeito de sair com
                                                        o ouro: sem memória, o agente
                                                        não sabe se já o pegou)
  R4  baque                                   → VIRAR (esquerda ou direita, ao acaso)
  R5  fedor ou brisa, 70% das vezes           → VIRAR (tenta não entrar no perigo)
  R6  caso geral, 75% das vezes               → AVANCAR, senão VIRAR

A aleatoriedade (reflexo aleatório, Russell & Norvig 2.4) é o que impede o agente
de ficar girando para sempre no mesmo lugar: um reativo determinístico sem memória
entra em ciclo com facilidade. O gerador de números fica no módulo, não em self,
então nenhuma informação sobre o mundo é guardada entre as chamadas.

Por que ele perde (para o relatório):
  - não lembra onde já esteve nem onde sentiu brisa, então cedo ou tarde anda para
    dentro de um poço ou do Wumpus (R5 só diminui a chance);
  - não sabe que já está com o ouro, então não "volta" para (1,1): só sai com o
    ouro se passar por lá por acaso (R3);
  - mundos com brisa/fedor em (1,1) fazem ele sair logo (R2): pontuação ≈ 0, mas
    sem nunca pegar o ouro.
"""

import random

from wumpus import Acao, Agente, Percepcao

INICIO = (1, 1)

# Semente fixa: o experimento dá o mesmo resultado a cada execução.
_ACASO = random.Random(2024)

_GIROS = (Acao.VIRAR_ESQUERDA, Acao.VIRAR_DIREITA)


class AgenteReativo(Agente):
    nome = "A · Reativo"

    def agir(self, percepcao: Percepcao) -> Acao:
        em_casa = percepcao.posicao == INICIO
        perigo = percepcao.fedor or percepcao.brisa

        if percepcao.brilho:                                   # R1
            return Acao.AGARRAR
        if em_casa and perigo:                                 # R2
            return Acao.SAIR
        if em_casa and _ACASO.random() < 0.15:                 # R3
            return Acao.SAIR
        if percepcao.baque:                                    # R4
            return _ACASO.choice(_GIROS)
        if perigo and _ACASO.random() < 0.70:                  # R5
            return _ACASO.choice(_GIROS)
        if _ACASO.random() < 0.75:                             # R6
            return Acao.AVANCAR
        return _ACASO.choice(_GIROS)
