"""Classe base de todos os agentes do trabalho.

Contrato (vale para os Agentes A, B, C e o bônus D):

  1. Herde de Agente e implemente agir(percepcao) -> Acao.
  2. O construtor NÃO recebe argumentos. O simulador cria uma instância NOVA
     para cada mundo, então qualquer memória vale só para aquela partida.
  3. O agente conhece o mundo apenas pela Percepcao recebida. Nada de ler o
     estado do simulador, variáveis globais compartilhadas ou arquivos com
     informações dos mundos.
  4. Defina o atributo `nome` (aparece na tabela do experimento).
  5. Opcional: implemente depurar() para mostrar o estado interno no jogar.py
     (por exemplo, as casas que a BC já provou seguras).
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from .acoes import Acao
from .percepcao import Percepcao


class Agente(ABC):
    nome: str = "Agente"

    def __init__(self) -> None:
        pass

    @abstractmethod
    def agir(self, percepcao: Percepcao) -> Acao:
        """Recebe a percepção atual e devolve a próxima ação."""

    def depurar(self) -> str:
        """Texto livre com o estado interno do agente (só para visualização)."""
        return ""
