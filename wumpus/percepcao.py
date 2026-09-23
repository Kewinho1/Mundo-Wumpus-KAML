"""Percepção entregue ao agente a cada passo (PEAS: Sensors)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from .acoes import Direcao


@dataclass(frozen=True)
class Percepcao:
    """Vetor de percepções do Mundo Wumpus (Russell & Norvig, cap. 7).

    Os cinco sensores clássicos:
      fedor  (FD) - o Wumpus está na casa atual ou numa casa vizinha (N, S, L, O)
      brisa  (BR) - há poço numa casa vizinha
      brilho (BL) - o ouro está na casa atual
      baque  (BQ) - a última ação AVANCAR bateu na parede
      grito  (GR) - a última ação ATIRAR matou o Wumpus (ouvido em toda a caverna)

    Propriocepção (simplificação didática, pode ser desligada pelo professor):
      posicao - (x, y) atual do agente, 1-indexado; (1,1) é o canto inferior esquerdo
      direcao - para onde o agente está virado
    Quando desligada, ambos chegam como None e o agente precisa rastrear a própria
    posição a partir das ações que executou (e do baque).
    """

    fedor: bool = False
    brisa: bool = False
    brilho: bool = False
    baque: bool = False
    grito: bool = False
    posicao: Optional[tuple[int, int]] = None
    direcao: Optional[Direcao] = None

    def como_vetor(self) -> list:
        """Formato do livro: [Stench, Breeze, Glitter, Bump, Scream] com None onde é falso."""
        nomes = ["Fedor", "Brisa", "Brilho", "Baque", "Grito"]
        valores = [self.fedor, self.brisa, self.brilho, self.baque, self.grito]
        return [n if v else None for n, v in zip(nomes, valores)]

    def descricao(self) -> str:
        """Percepção em linguagem natural (útil para o Agente D com LLM)."""
        partes = []
        if self.posicao is not None:
            partes.append(f"Você está na casa {self.posicao}, virado para o {self.direcao}.")
        sensacoes = {
            "fedor": "Você sente um fedor terrível.",
            "brisa": "Você sente uma brisa.",
            "brilho": "Você vê um brilho dourado nesta casa.",
            "baque": "Você acabou de bater numa parede.",
            "grito": "Você ouve um grito horrível ecoando pela caverna.",
        }
        ativas = [txt for campo, txt in sensacoes.items() if getattr(self, campo)]
        partes.extend(ativas or ["Você não percebe nada de especial."])
        return " ".join(partes)

    def __str__(self) -> str:
        siglas = [
            "FD" if self.fedor else "--",
            "BR" if self.brisa else "--",
            "BL" if self.brilho else "--",
            "BQ" if self.baque else "--",
            "GR" if self.grito else "--",
        ]
        texto = "[" + " ".join(siglas) + "]"
        if self.posicao is not None:
            texto += f" em {self.posicao} {self.direcao.seta}"
        return texto
