"""Testes do simulador (fornecidos pelo professor).

Rode com:  python -m unittest discover -s tests -v
Sugestão: criem também tests/test_logica.py para testar CNF e resolução do Agente B.
"""

import unittest

from wumpus import (Acao, Agente, Desfecho, Direcao, MundoWumpus,
                    acoes_para_vizinho, rodar_episodio, vizinhos)


class TestPercepcoes(unittest.TestCase):
    def setUp(self):
        self.m = MundoWumpus.classico()  # W(1,3) G(2,3) P(3,1) P(3,3) P(4,4)

    def test_inicio_sem_percepcoes(self):
        p = self.m.percepcao()
        self.assertFalse(any([p.fedor, p.brisa, p.brilho, p.baque, p.grito]))
        self.assertEqual(p.posicao, (1, 1))
        self.assertEqual(p.direcao, Direcao.LESTE)

    def test_brisa_em_2_1(self):
        p = self.m.executar(Acao.AVANCAR)
        self.assertEqual(p.posicao, (2, 1))
        self.assertTrue(p.brisa)
        self.assertFalse(p.fedor)

    def test_fedor_em_1_2(self):
        self.m.executar(Acao.VIRAR_ESQUERDA)
        p = self.m.executar(Acao.AVANCAR)
        self.assertEqual(p.posicao, (1, 2))
        self.assertTrue(p.fedor)
        self.assertFalse(p.brisa)

    def test_baque_na_parede(self):
        self.m.executar(Acao.VIRAR_DIREITA)  # SUL
        p = self.m.executar(Acao.AVANCAR)
        self.assertTrue(p.baque)
        self.assertEqual(p.posicao, (1, 1))
        p = self.m.executar(Acao.VIRAR_ESQUERDA)
        self.assertFalse(p.baque)  # baque só dura um passo

    def test_sem_posicao(self):
        m = MundoWumpus.classico(fornecer_posicao=False)
        p = m.percepcao()
        self.assertIsNone(p.posicao)
        self.assertIsNone(p.direcao)


class TestDinamica(unittest.TestCase):
    def test_flecha_mata_wumpus(self):
        m = MundoWumpus.classico()
        m.executar(Acao.VIRAR_ESQUERDA)  # NORTE, Wumpus em (1,3)
        p = m.executar(Acao.ATIRAR)
        self.assertTrue(p.grito)
        self.assertFalse(m.wumpus_vivo)
        self.assertEqual(m.pontuacao, -12)  # virar (-1) + atirar (-1) + flecha (-10)
        p = m.executar(Acao.ATIRAR)  # sem flecha: só -1
        self.assertFalse(p.grito)
        self.assertEqual(m.pontuacao, -13)

    def test_morte_no_poco(self):
        m = MundoWumpus.classico()
        m.executar(Acao.AVANCAR)
        m.executar(Acao.AVANCAR)  # (3,1) tem poço
        self.assertTrue(m.terminado)
        self.assertEqual(m.desfecho, Desfecho.CAIU_NO_POCO)
        self.assertEqual(m.pontuacao, -1002)

    def test_devorado(self):
        m = MundoWumpus.classico()
        for a in [Acao.VIRAR_ESQUERDA, Acao.AVANCAR, Acao.AVANCAR]:
            m.executar(a)
        self.assertEqual(m.desfecho, Desfecho.DEVORADO)

    def test_partida_perfeita_no_mundo_classico(self):
        m = MundoWumpus.classico()
        plano = [Acao.VIRAR_ESQUERDA, Acao.ATIRAR, Acao.AVANCAR, Acao.VIRAR_DIREITA,
                 Acao.AVANCAR, Acao.VIRAR_ESQUERDA, Acao.AVANCAR, Acao.AGARRAR,
                 Acao.VIRAR_ESQUERDA, Acao.VIRAR_ESQUERDA, Acao.AVANCAR, Acao.AVANCAR,
                 Acao.VIRAR_DIREITA, Acao.AVANCAR, Acao.SAIR]
        for a in plano:
            m.executar(a)
        self.assertTrue(m.sucesso)
        self.assertEqual(m.pontuacao, 1000 - len(plano) - 10)

    def test_sair_fora_de_1_1_nao_faz_nada(self):
        m = MundoWumpus.classico()
        m.executar(Acao.VIRAR_ESQUERDA)
        m.executar(Acao.AVANCAR)
        m.executar(Acao.SAIR)
        self.assertFalse(m.terminado)

    def test_limite_de_acoes(self):
        m = MundoWumpus.classico(limite_acoes=5)
        for _ in range(5):
            m.executar(Acao.VIRAR_DIREITA)
        self.assertEqual(m.desfecho, Desfecho.LIMITE_ACOES)


class TestGeracao(unittest.TestCase):
    def test_mesma_semente_mesmo_mundo(self):
        a, b = MundoWumpus.gerar(123), MundoWumpus.gerar(123)
        self.assertEqual((a.wumpus, a.ouro, a.pocos), (b.wumpus, b.ouro, b.pocos))

    def test_inicio_sempre_livre(self):
        for s in range(500):
            m = MundoWumpus.gerar(s)
            self.assertNotIn((1, 1), m.pocos)
            self.assertNotEqual(m.wumpus, (1, 1))
            self.assertNotEqual(m.ouro, (1, 1))


class TestAuxiliares(unittest.TestCase):
    def test_vizinhos(self):
        self.assertEqual(sorted(vizinhos((1, 1))), [(1, 2), (2, 1)])
        self.assertEqual(len(vizinhos((2, 2))), 4)

    def test_acoes_para_vizinho(self):
        self.assertEqual(acoes_para_vizinho((1, 1), Direcao.LESTE, (2, 1)), [Acao.AVANCAR])
        self.assertEqual(acoes_para_vizinho((1, 1), Direcao.LESTE, (1, 2)),
                         [Acao.VIRAR_ESQUERDA, Acao.AVANCAR])
        self.assertEqual(acoes_para_vizinho((2, 1), Direcao.LESTE, (1, 1)),
                         [Acao.VIRAR_DIREITA, Acao.VIRAR_DIREITA, Acao.AVANCAR])
        with self.assertRaises(ValueError):
            acoes_para_vizinho((1, 1), Direcao.LESTE, (3, 3))


class TestSimulador(unittest.TestCase):
    def test_erro_do_agente_vira_desfecho(self):
        class Quebrado(Agente):
            nome = "quebrado"

            def agir(self, percepcao):
                return "andar"  # não é Acao

        r = rodar_episodio(Quebrado, semente=0)
        self.assertEqual(r.desfecho, Desfecho.ERRO_AGENTE)
        self.assertIsNotNone(r.erro)
        self.assertEqual(r.pontuacao, -1000)


if __name__ == "__main__":
    unittest.main()
