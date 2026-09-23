"""Ações que o agente pode executar e direções em que pode estar virado."""

from __future__ import annotations

from enum import Enum


class Acao(Enum):
    """Atuadores do agente (PEAS: Actuators).

    Custos (medida de desempenho):
      - toda ação custa -1;
      - ATIRAR custa -10 adicionais (só na primeira vez, enquanto houver flecha);
      - SAIR em (1,1) com o ouro rende +1000.
    """

    AVANCAR = "avancar"                # anda uma casa na direção em que está virado
    VIRAR_ESQUERDA = "virar_esquerda"  # gira 90° no sentido anti-horário
    VIRAR_DIREITA = "virar_direita"    # gira 90° no sentido horário
    AGARRAR = "agarrar"                # pega o ouro, se ele estiver na casa atual
    ATIRAR = "atirar"                  # dispara a única flecha em linha reta
    SAIR = "sair"                      # sai da caverna (só funciona em (1,1))

    def __str__(self) -> str:
        return self.value


class Direcao(Enum):
    """Direções em sentido horário. O valor é o deslocamento (dx, dy)."""

    NORTE = (0, 1)
    LESTE = (1, 0)
    SUL = (0, -1)
    OESTE = (-1, 0)

    @property
    def delta(self) -> tuple[int, int]:
        return self.value

    def direita(self) -> "Direcao":
        ordem = list(Direcao)
        return ordem[(ordem.index(self) + 1) % 4]

    def esquerda(self) -> "Direcao":
        ordem = list(Direcao)
        return ordem[(ordem.index(self) - 1) % 4]

    @classmethod
    def de_delta(cls, delta: tuple[int, int]) -> "Direcao":
        """Direcao.de_delta((0, 1)) -> Direcao.NORTE"""
        return cls(tuple(delta))

    @property
    def seta(self) -> str:
        return {"NORTE": "^", "LESTE": ">", "SUL": "v", "OESTE": "<"}[self.name]

    def __str__(self) -> str:
        return self.name.lower()
