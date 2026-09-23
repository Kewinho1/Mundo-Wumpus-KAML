"""Simulador do Mundo Wumpus (padrão Russell & Norvig, cap. 7).

Convenções
----------
- Grade tamanho x tamanho (padrão 4x4), coordenadas (x, y) 1-indexadas.
  (1,1) é o canto inferior esquerdo; x cresce para a direita, y para cima.
- O agente começa em (1,1), virado para o LESTE, com uma flecha.
- 1 Wumpus e 1 ouro sorteados entre as casas diferentes de (1,1).
- Cada casa diferente de (1,1) tem poço com probabilidade 0,2.
- Como no livro, o ouro pode cair numa casa com poço ou com o Wumpus:
  alguns mundos simplesmente não têm solução segura (isso entra na análise).

ATENÇÃO, GRUPOS: o agente só pode conhecer o mundo pela Percepcao que recebe.
Ler atributos do simulador (wumpus, pocos, ouro...) de dentro do agente é fraude.
"""

from __future__ import annotations

import random
from typing import Iterable, Optional

from .acoes import Acao, Direcao
from .percepcao import Percepcao

Posicao = tuple  # (x, y)

INICIO: Posicao = (1, 1)


class Desfecho:
    """Como um episódio pode terminar."""

    SAIU_COM_OURO = "saiu_com_ouro"
    SAIU_SEM_OURO = "saiu_sem_ouro"
    CAIU_NO_POCO = "caiu_no_poco"
    DEVORADO = "devorado_pelo_wumpus"
    LIMITE_ACOES = "limite_de_acoes"
    LIMITE_TEMPO = "limite_de_tempo"
    ERRO_AGENTE = "erro_do_agente"

    MORTES = frozenset({CAIU_NO_POCO, DEVORADO})
    TODOS = (SAIU_COM_OURO, SAIU_SEM_OURO, CAIU_NO_POCO, DEVORADO,
             LIMITE_ACOES, LIMITE_TEMPO, ERRO_AGENTE)


# --------------------------------------------------------------------------
# Funções auxiliares (podem ser usadas livremente pelos agentes)
# --------------------------------------------------------------------------

def vizinhos(pos: Posicao, tamanho: int = 4) -> list:
    """Casas adjacentes (N, L, S, O) dentro da grade."""
    x, y = pos
    candidatas = [(x, y + 1), (x + 1, y), (x, y - 1), (x - 1, y)]
    return [(a, b) for a, b in candidatas if 1 <= a <= tamanho and 1 <= b <= tamanho]


def acoes_para_vizinho(origem: Posicao, direcao: Direcao, destino: Posicao) -> list:
    """Sequência mínima de ações para ir de `origem` a uma casa ADJACENTE `destino`.

    Exemplo: em (1,1) virado para LESTE, ir para (1,2) -> [VIRAR_ESQUERDA, AVANCAR].
    Útil para transformar o caminho devolvido pela BFS em ações.
    """
    delta = (destino[0] - origem[0], destino[1] - origem[1])
    try:
        alvo = Direcao.de_delta(delta)
    except ValueError:
        raise ValueError(f"{destino} não é adjacente a {origem}") from None
    if alvo == direcao:
        giros = []
    elif alvo == direcao.direita():
        giros = [Acao.VIRAR_DIREITA]
    elif alvo == direcao.esquerda():
        giros = [Acao.VIRAR_ESQUERDA]
    else:
        giros = [Acao.VIRAR_DIREITA, Acao.VIRAR_DIREITA]
    return giros + [Acao.AVANCAR]


# --------------------------------------------------------------------------
# O ambiente
# --------------------------------------------------------------------------

class MundoWumpus:
    """Ambiente parcialmente observável, determinístico, sequencial, estático,
    discreto e de agente único."""

    RECOMPENSA_OURO = 1000   # sair em (1,1) com o ouro
    PENALIDADE_MORTE = -1000  # cair em poço ou ser devorado
    CUSTO_ACAO = -1          # toda ação
    CUSTO_FLECHA = -10       # adicional ao usar a flecha

    def __init__(
        self,
        wumpus: Posicao,
        ouro: Posicao,
        pocos: Iterable[Posicao] = (),
        tamanho: int = 4,
        limite_acoes: int = 250,
        fornecer_posicao: bool = True,
        semente: Optional[int] = None,
    ):
        self.tamanho = tamanho
        self.wumpus = tuple(wumpus)
        self.ouro = tuple(ouro)
        self.pocos = frozenset(tuple(p) for p in pocos)
        self.limite_acoes = limite_acoes
        self.fornecer_posicao = fornecer_posicao
        self.semente = semente

        for casa in [self.wumpus, self.ouro, *self.pocos]:
            if not self._dentro(casa):
                raise ValueError(f"Casa {casa} fora da grade {tamanho}x{tamanho}")
        if INICIO in self.pocos or self.wumpus == INICIO:
            raise ValueError("(1,1) não pode ter poço nem Wumpus")

        # Estado dinâmico
        self.posicao: Posicao = INICIO
        self.direcao: Direcao = Direcao.LESTE
        self.tem_flecha = True
        self.tem_ouro = False
        self.wumpus_vivo = True
        self.ouro_no_chao = True
        self.pontuacao = 0
        self.acoes = 0
        self.terminado = False
        self.desfecho: Optional[str] = None
        self.visitadas = {INICIO}
        self.historico: list = []
        self._baque = False
        self._grito = False

    # ------------------------------------------------------------ construtores

    @classmethod
    def gerar(cls, semente: int, tamanho: int = 4, prob_poco: float = 0.2, **kwargs) -> "MundoWumpus":
        """Gera um mundo aleatório, sempre o mesmo para a mesma semente."""
        rng = random.Random(semente)
        casas = [(x, y) for x in range(1, tamanho + 1) for y in range(1, tamanho + 1)
                 if (x, y) != INICIO]
        wumpus = rng.choice(casas)
        ouro = rng.choice(casas)
        pocos = [c for c in casas if rng.random() < prob_poco]
        return cls(wumpus, ouro, pocos, tamanho=tamanho, semente=semente, **kwargs)

    @classmethod
    def classico(cls, **kwargs) -> "MundoWumpus":
        """O mundo da figura 7.2 do Russell & Norvig (bom para depurar o Agente B)."""
        return cls(wumpus=(1, 3), ouro=(2, 3), pocos=[(3, 1), (3, 3), (4, 4)], **kwargs)

    # ------------------------------------------------------------ percepção

    def percepcao(self) -> Percepcao:
        pos = self.posicao
        adj = vizinhos(pos, self.tamanho)
        return Percepcao(
            fedor=self.wumpus == pos or self.wumpus in adj,
            brisa=any(c in self.pocos for c in adj),
            brilho=self.ouro_no_chao and self.ouro == pos,
            baque=self._baque,
            grito=self._grito,
            posicao=pos if self.fornecer_posicao else None,
            direcao=self.direcao if self.fornecer_posicao else None,
        )

    # ------------------------------------------------------------ dinâmica

    def executar(self, acao: Acao) -> Percepcao:
        """Aplica a ação, atualiza a pontuação e devolve a nova percepção."""
        if self.terminado:
            raise RuntimeError("O episódio já terminou")
        if not isinstance(acao, Acao):
            raise TypeError(f"Ação inválida: {acao!r} (use um membro de wumpus.Acao)")

        self.acoes += 1
        self.pontuacao += self.CUSTO_ACAO
        self._baque = self._grito = False
        self.historico.append(acao)

        if acao is Acao.AVANCAR:
            dx, dy = self.direcao.delta
            nova = (self.posicao[0] + dx, self.posicao[1] + dy)
            if self._dentro(nova):
                self.posicao = nova
                self.visitadas.add(nova)
                if nova in self.pocos:
                    self.encerrar(Desfecho.CAIU_NO_POCO, self.PENALIDADE_MORTE)
                elif nova == self.wumpus and self.wumpus_vivo:
                    self.encerrar(Desfecho.DEVORADO, self.PENALIDADE_MORTE)
            else:
                self._baque = True

        elif acao is Acao.VIRAR_ESQUERDA:
            self.direcao = self.direcao.esquerda()

        elif acao is Acao.VIRAR_DIREITA:
            self.direcao = self.direcao.direita()

        elif acao is Acao.AGARRAR:
            if self.ouro_no_chao and self.posicao == self.ouro:
                self.ouro_no_chao = False
                self.tem_ouro = True

        elif acao is Acao.ATIRAR:
            if self.tem_flecha:
                self.tem_flecha = False
                self.pontuacao += self.CUSTO_FLECHA
                self._disparar_flecha()

        elif acao is Acao.SAIR:
            if self.posicao == INICIO:
                if self.tem_ouro:
                    self.encerrar(Desfecho.SAIU_COM_OURO, self.RECOMPENSA_OURO)
                else:
                    self.encerrar(Desfecho.SAIU_SEM_OURO)

        if not self.terminado and self.acoes >= self.limite_acoes:
            self.encerrar(Desfecho.LIMITE_ACOES)

        return self.percepcao()

    def encerrar(self, desfecho: str, penalidade: int = 0) -> None:
        """Termina o episódio (usado internamente e pelo simulador)."""
        if self.terminado:
            return
        self.terminado = True
        self.desfecho = desfecho
        self.pontuacao += penalidade

    def _disparar_flecha(self) -> None:
        dx, dy = self.direcao.delta
        x, y = self.posicao[0] + dx, self.posicao[1] + dy
        while self._dentro((x, y)):
            if (x, y) == self.wumpus and self.wumpus_vivo:
                self.wumpus_vivo = False
                self._grito = True
                return
            x, y = x + dx, y + dy

    def _dentro(self, pos: Posicao) -> bool:
        return 1 <= pos[0] <= self.tamanho and 1 <= pos[1] <= self.tamanho

    # ------------------------------------------------------------ resultados

    @property
    def sucesso(self) -> bool:
        return self.desfecho == Desfecho.SAIU_COM_OURO

    @property
    def morreu(self) -> bool:
        return self.desfecho in Desfecho.MORTES

    # ------------------------------------------------------------ visualização

    def desenhar(self, revelar: bool = True) -> str:
        """Desenho em ASCII. revelar=False mostra só o que o agente já visitou."""
        largura = 9
        separador = "    +" + ("-" * largura + "+") * self.tamanho
        linhas = [separador]
        for y in range(self.tamanho, 0, -1):
            celulas = []
            for x in range(1, self.tamanho + 1):
                casa = (x, y)
                tokens = []
                if casa == self.posicao:
                    tokens.append("A" + self.direcao.seta)
                if revelar:
                    if casa == self.wumpus:
                        tokens.append("W" if self.wumpus_vivo else "w")
                    if casa in self.pocos:
                        tokens.append("P")
                    if casa == self.ouro and self.ouro_no_chao:
                        tokens.append("G")
                elif casa not in self.visitadas:
                    tokens.append("?")
                if not tokens and casa in self.visitadas:
                    tokens.append("·")
                celulas.append(" ".join(tokens).center(largura))
            linhas.append(f"{y:>3} |" + "|".join(celulas) + "|")
            linhas.append(separador)
        linhas.append("     " + "".join(str(x).center(largura) + " " for x in range(1, self.tamanho + 1)))

        status = (f"Pontuação: {self.pontuacao}  |  Ações: {self.acoes}  |  "
                  f"Flecha: {'sim' if self.tem_flecha else 'não'}  |  "
                  f"Ouro: {'sim' if self.tem_ouro else 'não'}")
        if revelar:
            status += f"  |  Wumpus: {'vivo' if self.wumpus_vivo else 'morto'}"
        linhas.append(status)
        if revelar:
            linhas.append("Legenda: A agente · W Wumpus (w = morto) · P poço · G ouro · '·' visitada")
        else:
            linhas.append("Legenda: A agente · '·' visitada · ? desconhecida")
        if self.terminado:
            linhas.append(f"FIM: {self.desfecho}")
        return "\n".join(linhas)

    def __str__(self) -> str:
        return self.desenhar(revelar=True)
