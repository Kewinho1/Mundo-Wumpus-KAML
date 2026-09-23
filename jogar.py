#!/usr/bin/env python3
"""Jogue você mesmo ou assista um agente jogando, passo a passo.

Exemplos
--------
  python jogar.py --humano                     # você joga (vê só o que já visitou)
  python jogar.py --humano --semente 7
  python jogar.py --agente B --classico        # agente B no mundo da figura 7.2 do livro
  python jogar.py --agente C --semente 13 --pausa 0.4
  python jogar.py --agente agentes.meu_agente:MeuAgente --nevoa

Controles do modo humano:
  w avançar · a virar à esquerda · d virar à direita
  g agarrar · f atirar a flecha · s sair · q desistir
"""

import argparse
import sys
import time

from agentes import REGISTRO
from wumpus import Acao, Agente, MundoWumpus, Percepcao, carregar_agente

TECLAS = {
    "w": Acao.AVANCAR,
    "a": Acao.VIRAR_ESQUERDA,
    "d": Acao.VIRAR_DIREITA,
    "g": Acao.AGARRAR,
    "f": Acao.ATIRAR,
    "s": Acao.SAIR,
}


class AgenteHumano(Agente):
    nome = "Humano"

    def agir(self, percepcao: Percepcao) -> Acao:
        while True:
            tecla = input("Ação [w a d g f s | q]: ").strip().lower()
            if tecla == "q":
                raise KeyboardInterrupt
            if tecla in TECLAS:
                return TECLAS[tecla]
            print("  Tecla inválida.")


def mostrar(mundo: MundoWumpus, percepcao: Percepcao, revelar: bool,
            acao=None, agente=None) -> None:
    print("\n" + "=" * 50)
    if acao is not None:
        print(f"Ação #{mundo.acoes}: {acao}")
    print(mundo.desenhar(revelar=revelar))
    print(f"Percepção: {percepcao}")
    print(f"           {percepcao.descricao()}")
    if agente is not None:
        info = agente.depurar()
        if info:
            print(f"Agente:    {info}")


def main() -> int:
    p = argparse.ArgumentParser(description="Mundo Wumpus interativo")
    quem = p.add_mutually_exclusive_group(required=True)
    quem.add_argument("--humano", action="store_true", help="você joga pelo teclado")
    quem.add_argument("--agente", help=f"atalho {list(REGISTRO)} ou modulo:Classe")
    p.add_argument("--semente", type=int, default=0, help="semente do mundo (padrão 0)")
    p.add_argument("--classico", action="store_true", help="usa o mundo da figura 7.2 do livro")
    p.add_argument("--pausa", type=float, default=None,
                   help="segundos entre passos do agente (padrão: tecle Enter a cada passo)")
    p.add_argument("--nevoa", action="store_true",
                   help="ao assistir um agente, esconde o que ele não visitou")
    p.add_argument("--sem-posicao", action="store_true", help="percepção sem posição/direção")
    args = p.parse_args()

    opcoes = {"fornecer_posicao": not args.sem_posicao}
    mundo = MundoWumpus.classico(**opcoes) if args.classico else MundoWumpus.gerar(args.semente, **opcoes)

    if args.humano:
        agente, revelar = AgenteHumano(), False
    else:
        agente, revelar = carregar_agente(args.agente, REGISTRO)(), not args.nevoa

    percepcao = mundo.percepcao()
    mostrar(mundo, percepcao, revelar, agente=agente)
    try:
        while not mundo.terminado:
            if not args.humano:
                if args.pausa is None:
                    input("[Enter] próximo passo ")
                else:
                    time.sleep(args.pausa)
            acao = agente.agir(percepcao)
            percepcao = mundo.executar(acao)
            mostrar(mundo, percepcao, revelar, acao=acao, agente=agente)
    except (KeyboardInterrupt, EOFError):
        print("\nPartida interrompida.")
        return 1

    print("\n" + "=" * 50 + "\nMUNDO REVELADO")
    print(mundo.desenhar(revelar=True))
    print(f"\nResultado: {mundo.desfecho} · pontuação {mundo.pontuacao} · {mundo.acoes} ações")
    return 0


if __name__ == "__main__":
    sys.exit(main())
