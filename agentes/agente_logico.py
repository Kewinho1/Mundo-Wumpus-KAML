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

Dica de engenharia (slide 09): instancie as regras B e F apenas para as casas já
visitadas e guarde em cache as respostas de ask(). A BC enxuta é o que torna a
resolução tratável.

Liberdade de projeto: a representação de sentenças, literais e cláusulas é do grupo.
Uma sugestão simples é literal = (simbolo, positivo), por exemplo ("P13", False)
para ¬P(1,3), e cláusula = frozenset de literais. Justifique a escolha no relatório.
"""

from wumpus import Acao, Agente, Percepcao, vizinhos, acoes_para_vizinho  # noqa: F401


class BaseConhecimento:
    """BC proposicional em CNF com TELL/ASK."""

    def __init__(self):
        self.clausulas = set()
        self._cache = {}

    def tell(self, sentenca) -> None:
        """Converte a sentença para CNF e acrescenta as cláusulas à BC."""
        # TODO (grupo)
        raise NotImplementedError

    def ask(self, consulta) -> bool:
        """True se BC ⊨ consulta, provado por resolução por refutação."""
        # TODO (grupo): lembre de invalidar/atualizar o cache quando a BC mudar.
        raise NotImplementedError


def para_cnf(sentenca):
    """Eliminar ⇔ e ⇒, empurrar ¬ para dentro (De Morgan), distribuir ∨ sobre ∧."""
    # TODO (grupo)
    raise NotImplementedError


def resolver(ci, cj):
    """Todos os resolventes possíveis entre as cláusulas ci e cj."""
    # TODO (grupo)
    raise NotImplementedError


def pl_resolucao(clausulas, consulta) -> bool:
    """PL-RESOLUTION (Russell & Norvig, fig. 7.12)."""
    # TODO (grupo)
    raise NotImplementedError


class AgenteLogico(Agente):
    nome = "B · Lógico"

    def __init__(self):
        super().__init__()
        self.bc = BaseConhecimento()
        self.tamanho = 4
        # TODO (grupo): axiomas iniciais (¬P(1,1), ¬W(1,1), ...) via self.bc.tell(...)
        # TODO (grupo): estado do agente (casas visitadas, seguras, se tem o ouro, ...)

    def agir(self, percepcao: Percepcao) -> Acao:
        # 1. TELL: registrar a percepção da casa atual na BC
        # 2. ASK:  descobrir quais casas vizinhas são seguras
        # 3. Decidir: agarrar, andar para uma casa segura, voltar ou sair
        # TODO (grupo)
        raise NotImplementedError("Agente B ainda não implementado")

    def depurar(self) -> str:
        return f"Cláusulas na BC: {len(self.bc.clausulas)}"
