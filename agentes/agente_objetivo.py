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

Decisão tomada (utilidade esperada)
-----------------------------------
Quando não há casa segura para explorar e o agente não tem o ouro:

1. ATIRAR, se existir uma casa da fronteira provada SEM POÇO (ask(¬P)) cujo único
   risco é o Wumpus. Custo: −10 da flecha, mais os giros/passos até a posição de
   tiro. Ganho: se houver grito, o Wumpus morre e todas as casas "só com risco de
   Wumpus" viram seguras; sem grito, a BC aprende ¬W em toda a linha da flecha e a
   casa-alvo vira segura do mesmo jeito. Nos dois casos a exploração continua sem
   nenhum risco de morte, e a chance de chegar ao ouro (+1000) justifica os ~−15.

2. Senão, VOLTAR para (1,1) e SAIR. Arriscar uma casa incerta tem utilidade esperada
   negativa: cada casa tem poço com probabilidade 0,2 e, numa casa de fronteira com
   brisa ao lado, essa probabilidade condicional passa de 0,3 com facilidade. Com
   p ≥ 0,3, o risco de −1000 já anula o ganho esperado, que é bem menor que +1000
   porque o ouro nem sempre está atrás daquela casa (e às vezes está num poço).
"""

from collections import deque

from wumpus import Acao, Percepcao, acoes_para_vizinho, vizinhos

from agentes.agente_logico import INICIO, AgenteLogico


class AgenteObjetivo(AgenteLogico):
    nome = "C · Lógico + BFS"

    def __init__(self):
        super().__init__()
        self.fase = "explorar"
        self.plano = []  # fila de ações já planejadas

    def bfs(self, origem, destinos, permitidas):
        """Menor caminho (lista de casas) de `origem` até alguma casa de `destinos`,
        andando só por casas em `permitidas`. Devolve None se não houver caminho."""
        destinos = set(destinos)
        pais = {origem: None}
        fila = deque([origem])
        while fila:
            casa = fila.popleft()
            if casa in destinos:
                caminho = []
                while casa is not None:
                    caminho.append(casa)
                    casa = pais[casa]
                return caminho[::-1]
            for v in vizinhos(casa, self.tamanho):
                if v not in pais and (v in permitidas or v in destinos):
                    pais[v] = casa
                    fila.append(v)
        return None

    def _acoes_do_caminho(self, caminho):
        """Caminho de casas → giros + AVANCAR. Devolve (ações, direção final)."""
        acoes, direcao = [], self.dir
        for origem, destino in zip(caminho, caminho[1:]):
            passo = acoes_para_vizinho(origem, direcao, destino)
            for a in passo:
                if a is Acao.VIRAR_ESQUERDA:
                    direcao = direcao.esquerda()
                elif a is Acao.VIRAR_DIREITA:
                    direcao = direcao.direita()
            acoes += passo
        return acoes, direcao

    def _fronteira(self):
        """Casas não visitadas vizinhas de alguma casa visitada."""
        return {v for c in self.visitadas for v in vizinhos(c, self.tamanho)
                if v not in self.visitadas}

    def agir(self, percepcao: Percepcao) -> Acao:
        # TELL (herdado do B), depois fase → plano → ação
        self._perceber(percepcao)
        return self._registrar(self._decidir(percepcao))

    def _decidir(self, percepcao: Percepcao) -> Acao:
        if self.plano:
            return self.plano.pop(0)

        if percepcao.brilho and not self.tem_ouro:
            self.fase = "agarrar"
            self.tem_ouro = True
            return Acao.AGARRAR

        if not self.tem_ouro:
            # EXPLORAR: BFS até a casa segura (provada por ask) mais próxima.
            fronteira = sorted(self._fronteira())
            seguras = [c for c in fronteira if self.seguro(c)]
            if seguras:
                self.fase = "explorar"
                return self._seguir(self.bfs(self.pos, seguras, self.visitadas))

            # Dilema do risco, opção 1: atirar numa casa que só pode ter o Wumpus.
            if self.tem_flecha:
                alvos = [c for c in fronteira if self.sem_poco(c)]
                plano = self._plano_de_tiro(alvos)
                if plano:
                    self.fase = "atirar"
                    self.plano = plano
                    return self.plano.pop(0)

        # VOLTAR (com o ouro, ou sem opção segura) e SAIR.
        self.fase = "voltar" if self.tem_ouro else "desistir"
        if self.pos == INICIO:
            self.fase = "sair"
            return Acao.SAIR
        return self._seguir(self.bfs(self.pos, {INICIO}, self.visitadas))

    def _seguir(self, caminho) -> Acao:
        self.plano, _ = self._acoes_do_caminho(caminho)
        return self.plano.pop(0)

    def _plano_de_tiro(self, alvos):
        """Vai até a casa visitada mais próxima vizinha de um alvo, vira para ele e atira."""
        postos = {}
        for alvo in alvos:
            for v in vizinhos(alvo, self.tamanho):
                if v in self.visitadas:
                    postos.setdefault(v, alvo)
        if not postos:
            return None
        caminho = self.bfs(self.pos, postos, self.visitadas)
        if caminho is None:
            return None
        posto = caminho[-1]
        acoes, direcao = self._acoes_do_caminho(caminho)
        giros = acoes_para_vizinho(posto, direcao, postos[posto])[:-1]  # sem o AVANCAR
        return acoes + giros + [Acao.ATIRAR]

    def depurar(self) -> str:
        return (f"Fase: {self.fase} | Plano: {[str(a) for a in self.plano]}\n"
                + super().depurar().split("\nPilha")[0])
