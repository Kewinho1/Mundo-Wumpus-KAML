"""Testes da base de conhecimento (CNF + resolução) e dos agentes B e C."""

import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from agentes.agente_logico import (AgenteLogico, BaseConhecimento, P, W, e, nao, ou,  # noqa: E402
                                   para_cnf, pl_resolucao, resolver, sse)
from agentes.agente_objetivo import AgenteObjetivo  # noqa: E402
from wumpus import MundoWumpus, rodar_episodio  # noqa: E402


class TestCNF(unittest.TestCase):
    def test_simbolo(self):
        self.assertEqual(para_cnf("A"), {frozenset({("A", True)})})

    def test_bicondicional(self):
        # B ⇔ (P1 ∨ P2)  =  (¬B ∨ P1 ∨ P2) ∧ (¬P1 ∨ B) ∧ (¬P2 ∨ B)
        esperado = {
            frozenset({("B", False), ("P1", True), ("P2", True)}),
            frozenset({("P1", False), ("B", True)}),
            frozenset({("P2", False), ("B", True)}),
        }
        self.assertEqual(para_cnf(sse("B", ou("P1", "P2"))), esperado)

    def test_de_morgan(self):
        self.assertEqual(para_cnf(nao(e("A", "B"))), {frozenset({("A", False), ("B", False)})})

    def test_implicacao(self):
        self.assertEqual(para_cnf(("implica", "A", "B")), {frozenset({("A", False), ("B", True)})})

    def test_dupla_negacao(self):
        self.assertEqual(para_cnf(nao(nao("A"))), {frozenset({("A", True)})})

    def test_distribuicao(self):
        # A ∨ (B ∧ C)  =  (A ∨ B) ∧ (A ∨ C)
        esperado = {frozenset({("A", True), ("B", True)}), frozenset({("A", True), ("C", True)})}
        self.assertEqual(para_cnf(ou("A", e("B", "C"))), esperado)


class TestResolucao(unittest.TestCase):
    def test_resolvente(self):
        ci = frozenset({("A", True), ("B", True)})
        cj = frozenset({("A", False), ("C", True)})
        self.assertEqual(resolver(ci, cj), [frozenset({("B", True), ("C", True)})])

    def test_sem_tautologia(self):
        ci = frozenset({("A", True), ("B", True)})
        cj = frozenset({("A", False), ("B", False)})
        self.assertEqual(resolver(ci, cj), [])

    def test_modus_ponens(self):
        bc = para_cnf(("implica", "A", "B")) | para_cnf("A")
        self.assertTrue(pl_resolucao(bc, "B"))
        self.assertFalse(pl_resolucao(bc, nao("B")))

    def test_nao_prova_o_que_nao_segue(self):
        bc = para_cnf(ou("A", "B"))
        self.assertFalse(pl_resolucao(bc, "A"))
        self.assertFalse(pl_resolucao(bc, nao("A")))


class TestExemploDoLivro(unittest.TestCase):
    """Figura 7.2/7.4 do Russell & Norvig: depois de visitar (1,1), (2,1) e (1,2)."""

    def setUp(self):
        self.bc = BaseConhecimento()
        casas = {  # casa: (brisa, fedor)
            (1, 1): (False, False),
            (2, 1): (True, False),
            (1, 2): (False, True),
        }
        viz = {(1, 1): [(1, 2), (2, 1)], (2, 1): [(1, 1), (3, 1), (2, 2)],
               (1, 2): [(1, 1), (1, 3), (2, 2)]}
        for c, (brisa, fedor) in casas.items():
            self.bc.tell(nao(P(c)))
            self.bc.tell(nao(W(c)))
            self.bc.tell(sse(f"B{c[0]}{c[1]}", ou(*(P(v) for v in viz[c]))))
            self.bc.tell(sse(f"F{c[0]}{c[1]}", ou(W(c), *(W(v) for v in viz[c]))))
            self.bc.tell(f"B{c[0]}{c[1]}" if brisa else nao(f"B{c[0]}{c[1]}"))
            self.bc.tell(f"F{c[0]}{c[1]}" if fedor else nao(f"F{c[0]}{c[1]}"))

    def test_deducoes_classicas(self):
        self.assertTrue(self.bc.ask(nao(P((2, 2)))))   # (2,2) sem poço
        self.assertTrue(self.bc.ask(nao(W((2, 2)))))   # e sem Wumpus
        self.assertTrue(self.bc.ask(P((3, 1))))        # poço em (3,1)
        self.assertTrue(self.bc.ask(W((1, 3))))        # Wumpus em (1,3)

    def test_nao_deduz_demais(self):
        self.assertFalse(self.bc.ask(P((2, 3))))
        self.assertFalse(self.bc.ask(nao(P((2, 3)))))


class TestAgentes(unittest.TestCase):
    def test_classico(self):
        for classe in (AgenteLogico, AgenteObjetivo):
            r = rodar_episodio(classe, mundo=MundoWumpus.classico())
            self.assertIsNone(r.erro, r.erro)
            self.assertEqual(r.desfecho, "saiu_com_ouro", classe.nome)

    def test_nunca_morrem_nem_dao_erro(self):
        for classe in (AgenteLogico, AgenteObjetivo):
            for semente in range(100):
                for posicao in (True, False):
                    r = rodar_episodio(classe, semente, fornecer_posicao=posicao)
                    self.assertIsNone(r.erro, r.erro)
                    self.assertFalse(r.morte, f"{classe.nome} morreu na semente {semente}")


if __name__ == "__main__":
    unittest.main()
