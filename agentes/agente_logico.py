"""AGENTE B — Agente lógico baseado em conhecimento (Aula 6).        [1,3 ponto]

Ciclo: PERCEPÇÃO → TELL → BC → ASK (resolução) → AÇÃO

Critérios de avaliação (slide 08):
  1. Axiomas gerados por código para as casas (nada escrito à mão casa a casa):
        ¬P(1,1)   ¬W(1,1)
        B(x,y) ⇔ P(vizinhos)   em disjunção
        F(x,y) ⇔ W(vizinhos)   em disjunção
  2. Percepções entram na BC SOMENTE via tell().
  3. A segurança de uma casa é decidida SOMENTE via ask(), por resolução por
     refutação: BC ∧ ¬α ⊢ □ (cláusula vazia)  ⇒  BC ⊨ α.
  4. Nada de "if brisa: evitar vizinhos" escondido no código.

Regras do jogo (slide 13):
  - A conversão para CNF e a resolução são implementadas pelo grupo.
  - sympy, pysat e z3 NÃO podem ser usados aqui; só em testes, para conferir resultados.

Representação escolhida
-----------------------
Sentença: um símbolo é uma string ("P13", "B21", "WumpusVivo"); sentenças compostas
são tuplas com o conectivo na frente:
    ("nao", s)   ("e", s1, s2, ...)   ("ou", s1, s2, ...)
    ("implica", a, b)   ("sse", a, b)
Literal: (simbolo, positivo), por exemplo ("P13", False) = ¬P(1,3).
Cláusula: frozenset de literais (a disjunção deles); frozenset() é a cláusula vazia □.
Tuplas e frozensets são imutáveis e "hasheáveis", então servem de chave no cache
de ask() e deixam a BC ser um conjunto sem cláusulas repetidas.

Símbolos
--------
    P{x}{y}  poço em (x,y)         B{x}{y}  brisa sentida em (x,y)
    W{x}{y}  Wumpus em (x,y)       F{x}{y}  fedor sentido em (x,y)
    WumpusVivo                     (vira falso quando ouvimos o grito)
Uma casa é segura quando BC ⊨ ¬P(x,y) e BC ⊨ ¬W(x,y) ∨ ¬WumpusVivo.

Estratégia de movimento do Agente B: busca em profundidade com retrocesso (DFS).
Anda para uma vizinha provada segura e ainda não visitada; se não houver, volta
pelo mesmo caminho (pilha). Com o ouro, desempilha tudo até (1,1) e sai.
O Agente C troca isso por BFS (caminhos mínimos) e decide sobre a flecha.
"""

from wumpus import Acao, Agente, Direcao, Percepcao, vizinhos, acoes_para_vizinho

INICIO = (1, 1)
VIVO = "WumpusVivo"


# --------------------------------------------------------------------------
# Construtores de sentenças (açúcar sintático para gerar os axiomas por código)
# --------------------------------------------------------------------------

def nao(s):
    return ("nao", s)


def e(*ss):
    return ("e", *ss)


def ou(*ss):
    return ("ou", *ss)


def sse(a, b):
    return ("sse", a, b)


def P(c):
    return f"P{c[0]}{c[1]}"


def W(c):
    return f"W{c[0]}{c[1]}"


def B(c):
    return f"B{c[0]}{c[1]}"


def F(c):
    return f"F{c[0]}{c[1]}"


# --------------------------------------------------------------------------
# CNF
# --------------------------------------------------------------------------

def _eliminar_implicacoes(s):
    """Passo 1: α ⇔ β  vira (¬α ∨ β) ∧ (¬β ∨ α);  α ⇒ β  vira ¬α ∨ β."""
    if isinstance(s, str):
        return s
    op, *args = s
    args = [_eliminar_implicacoes(a) for a in args]
    if op == "sse":
        a, b = args
        return ("e", ("ou", ("nao", a), b), ("ou", ("nao", b), a))
    if op == "implica":
        a, b = args
        return ("ou", ("nao", a), b)
    return (op, *args)


def _empurrar_negacao(s, negado=False):
    """Passo 2: De Morgan e dupla negação, até o ¬ ficar só na frente de símbolos."""
    if isinstance(s, str):
        return ("nao", s) if negado else s
    op, *args = s
    if op == "nao":
        return _empurrar_negacao(args[0], not negado)
    if op in ("e", "ou"):
        novo_op = {"e": "ou", "ou": "e"}[op] if negado else op
        return (novo_op, *(_empurrar_negacao(a, negado) for a in args))
    raise ValueError(f"Conectivo inesperado depois do passo 1: {op!r}")


def _tautologia(clausula) -> bool:
    return any((simbolo, not positivo) in clausula for simbolo, positivo in clausula)


def _distribuir(s) -> set:
    """Passo 3: distribui ∨ sobre ∧ e devolve o conjunto de cláusulas."""
    if isinstance(s, str):
        return {frozenset({(s, True)})}
    op, *args = s
    if op == "nao":                       # aqui args[0] é sempre um símbolo
        return {frozenset({(args[0], False)})}
    if op == "e":
        clausulas = set()
        for a in args:
            clausulas |= _distribuir(a)
        return clausulas
    if op == "ou":
        clausulas = {frozenset()}
        for a in args:
            clausulas = {c1 | c2 for c1 in clausulas for c2 in _distribuir(a)}
        return {c for c in clausulas if not _tautologia(c)}
    raise ValueError(f"Conectivo inesperado: {op!r}")


def para_cnf(sentenca) -> set:
    """Eliminar ⇔ e ⇒, empurrar ¬ para dentro (De Morgan), distribuir ∨ sobre ∧.

    Devolve um conjunto de cláusulas (frozensets de literais).
    """
    return _distribuir(_empurrar_negacao(_eliminar_implicacoes(sentenca)))


# --------------------------------------------------------------------------
# Resolução
# --------------------------------------------------------------------------

def resolver(ci, cj) -> list:
    """Todos os resolventes possíveis entre as cláusulas ci e cj (sem tautologias)."""
    resolventes = []
    for simbolo, positivo in ci:
        complementar = (simbolo, not positivo)
        if complementar in cj:
            r = (ci - {(simbolo, positivo)}) | (cj - {complementar})
            if not _tautologia(r):
                resolventes.append(frozenset(r))
    return resolventes


def _simbolos(clausula):
    return {simbolo for simbolo, _ in clausula}


def _relevantes(clausulas, simbolos_iniciais) -> set:
    """Só as cláusulas ligadas (direta ou indiretamente) aos símbolos da consulta.

    Poços e Wumpus não compartilham símbolos, então uma pergunta sobre P nunca
    precisa olhar as cláusulas de W, e vice-versa. Isso não muda a resposta: uma
    cláusula sem nenhum símbolo em comum nunca participa da refutação.
    """
    simbolos = set(simbolos_iniciais)
    restantes = set(clausulas)
    escolhidas = set()
    mudou = True
    while mudou:
        mudou = False
        for c in list(restantes):
            if _simbolos(c) & simbolos:
                escolhidas.add(c)
                restantes.discard(c)
                simbolos |= _simbolos(c)
                mudou = True
    return escolhidas


def pl_resolucao(clausulas, consulta) -> bool:
    """PL-RESOLUTION (Russell & Norvig, fig. 7.12), com conjunto de suporte.

    Prova BC ⊨ α mostrando que BC ∧ ¬α é insatisfatível (chega na cláusula vazia).
    Estratégia de conjunto de suporte: toda resolução usa pelo menos uma cláusula
    que veio de ¬α ou de um resolvente anterior. É completa para refutação
    quando a BC sozinha é satisfatível, e a BC do agente sempre é (descreve o mundo
    real). Resolventes subsumidos por uma cláusula que já existe são descartados.
    """
    negacao = para_cnf(("nao", consulta))
    if frozenset() in negacao:
        return True
    simbolos = set().union(*(_simbolos(c) for c in negacao)) if negacao else set()
    todas = _relevantes(clausulas, simbolos) | negacao
    fila = list(negacao)
    i = 0
    while i < len(fila):
        ci = fila[i]
        i += 1
        for cj in list(todas):
            for r in resolver(ci, cj):
                if not r:
                    return True               # □: BC ∧ ¬α é contraditória
                if r in todas or any(c <= r for c in todas):
                    continue
                todas.add(r)
                fila.append(r)
    return False


class BaseConhecimento:
    """BC proposicional em CNF com TELL/ASK."""

    def __init__(self):
        self.clausulas = set()
        self._cache = {}
        self.consultas = 0   # quantas resoluções de verdade foram feitas (para o relatório)

    def tell(self, sentenca) -> None:
        """Converte a sentença para CNF e acrescenta as cláusulas à BC."""
        novas = para_cnf(sentenca) - self.clausulas
        if novas:
            self.clausulas |= novas
            # A BC só cresce, então o que já foi provado continua provado (monotonicidade).
            # Só as respostas "não sei" podem mudar: essas saem do cache.
            self._cache = {k: v for k, v in self._cache.items() if v}

    def ask(self, consulta) -> bool:
        """True se BC ⊨ consulta, provado por resolução por refutação."""
        if consulta not in self._cache:
            self.consultas += 1
            self._cache[consulta] = pl_resolucao(self.clausulas, consulta)
        return self._cache[consulta]


# --------------------------------------------------------------------------
# O agente
# --------------------------------------------------------------------------

class AgenteLogico(Agente):
    nome = "B · Lógico"

    def __init__(self):
        super().__init__()
        self.bc = BaseConhecimento()
        self.tamanho = 4
        # Axiomas iniciais: a casa de partida não tem poço nem Wumpus.
        self.bc.tell(nao(P(INICIO)))
        self.bc.tell(nao(W(INICIO)))

        # Estado do agente. A posição é rastreada pelas próprias ações (funciona
        # também com --sem-posicao); se a percepção trouxer a posição, ela confirma.
        self.pos = INICIO
        self.dir = Direcao.LESTE
        self.visitadas = set()
        self.tem_ouro = False
        self.tem_flecha = True
        self.plano = []        # ações já decididas, executadas uma por chamada
        self.caminho = []      # pilha da DFS: casas por onde viemos
        self._ultima = None    # última ação devolvida
        self._tiro = None      # (casa, direção) do disparo, para interpretar o grito

    # ------------------------------------------------------------ percepção → TELL

    def _perceber(self, percepcao: Percepcao) -> None:
        """Atualiza posição/direção e conta à BC tudo o que foi percebido."""
        if self._ultima is Acao.AVANCAR and not percepcao.baque:
            dx, dy = self.dir.delta
            self.pos = (self.pos[0] + dx, self.pos[1] + dy)
        if percepcao.posicao is not None:
            self.pos, self.dir = tuple(percepcao.posicao), percepcao.direcao

        if self.pos not in self.visitadas:
            self.visitadas.add(self.pos)
            self._tell_casa(self.pos, percepcao)

        if self._tiro is not None:
            self._tell_tiro(percepcao)
            self._tiro = None

    def _tell_casa(self, c, percepcao: Percepcao) -> None:
        """Axiomas da casa (gerados por código) + o que foi sentido nela."""
        adj = vizinhos(c, self.tamanho)
        # Estou vivo aqui: não há poço, e o Wumpus não está aqui (ou já morreu).
        self.bc.tell(nao(P(c)))
        self.bc.tell(ou(nao(W(c)), nao(VIVO)))
        # B(x,y) ⇔ P(vizinhos) e F(x,y) ⇔ W(casa ou vizinhos)
        self.bc.tell(sse(B(c), ou(*(P(v) for v in adj))))
        self.bc.tell(sse(F(c), ou(W(c), *(W(v) for v in adj))))
        # As percepções entram na BC só por aqui.
        self.bc.tell(B(c) if percepcao.brisa else nao(B(c)))
        self.bc.tell(F(c) if percepcao.fedor else nao(F(c)))

    def _tell_tiro(self, percepcao: Percepcao) -> None:
        """Grito ⇒ o Wumpus morreu.  Sem grito ⇒ o Wumpus não está na linha da flecha."""
        if percepcao.grito:
            self.bc.tell(nao(VIVO))
            return
        (x, y), (dx, dy) = self._tiro[0], self._tiro[1].delta
        x, y = x + dx, y + dy
        while 1 <= x <= self.tamanho and 1 <= y <= self.tamanho:
            self.bc.tell(nao(W((x, y))))
            x, y = x + dx, y + dy

    # ------------------------------------------------------------ ASK

    def sem_poco(self, c) -> bool:
        return self.bc.ask(nao(P(c)))

    def sem_wumpus(self, c) -> bool:
        return self.bc.ask(ou(nao(W(c)), nao(VIVO)))

    def seguro(self, c) -> bool:
        """Segurança decidida só por ask() (resolução por refutação)."""
        return self.sem_poco(c) and self.sem_wumpus(c)

    # ------------------------------------------------------------ ações

    def _registrar(self, acao: Acao) -> Acao:
        """Atualiza o estado interno com a ação que vai ser devolvida."""
        if acao is Acao.VIRAR_ESQUERDA:
            self.dir = self.dir.esquerda()
        elif acao is Acao.VIRAR_DIREITA:
            self.dir = self.dir.direita()
        elif acao is Acao.ATIRAR and self.tem_flecha:
            self.tem_flecha = False
            self._tiro = (self.pos, self.dir)
        self._ultima = acao
        return acao

    def _ir_para_vizinho(self, destino) -> Acao:
        self.plano = acoes_para_vizinho(self.pos, self.dir, destino)
        return self.plano.pop(0)

    def agir(self, percepcao: Percepcao) -> Acao:
        # 1. TELL: registrar a percepção da casa atual na BC
        self._perceber(percepcao)
        # 2 e 3. ASK + decidir
        return self._registrar(self._decidir(percepcao))

    def _decidir(self, percepcao: Percepcao) -> Acao:
        if self.plano:
            return self.plano.pop(0)
        if percepcao.brilho and not self.tem_ouro:
            self.tem_ouro = True
            return Acao.AGARRAR
        if not self.tem_ouro:
            # ASK: quais vizinhas não visitadas são seguras? (as de frente primeiro)
            candidatas = [v for v in vizinhos(self.pos, self.tamanho) if v not in self.visitadas]
            candidatas.sort(key=lambda v: len(acoes_para_vizinho(self.pos, self.dir, v)))
            for v in candidatas:
                if self.seguro(v):
                    self.caminho.append(self.pos)
                    return self._ir_para_vizinho(v)
        # Com o ouro, ou sem vizinha segura: volta pelo caminho (retrocesso da DFS).
        if self.caminho:
            return self._ir_para_vizinho(self.caminho.pop())
        return Acao.SAIR   # pilha vazia = estou em (1,1)

    def depurar(self) -> str:
        seguras = sorted(c for c, ok in self._seguras_conhecidas().items() if ok)
        return (f"Pos {self.pos} {self.dir.seta} | ouro: {'sim' if self.tem_ouro else 'não'}"
                f" | cláusulas na BC: {len(self.bc.clausulas)} | resoluções: {self.bc.consultas}\n"
                f"Seguras provadas (não visitadas): {seguras or '-'}\n"
                f"Pilha da DFS: {self.caminho}")

    def _seguras_conhecidas(self) -> dict:
        """Só lê o cache do ask() (não dispara resolução nova só para mostrar na tela)."""
        cache = self.bc._cache
        resultado = {}
        for x in range(1, self.tamanho + 1):
            for y in range(1, self.tamanho + 1):
                c = (x, y)
                if c not in self.visitadas:
                    resultado[c] = (cache.get(nao(P(c))) is True
                                    and cache.get(ou(nao(W(c)), nao(VIVO))) is True)
        return resultado
