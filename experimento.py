#!/usr/bin/env python3
"""Experimento comparativo: todos os agentes nos MESMOS mundos.

Exemplos
--------
  python experimento.py                         # A, B e C nas 200 sementes públicas
  python experimento.py aleatorio A B C --csv resultados.csv
  python experimento.py agentes.meu_agente:MeuAgente -n 50

Avaliação (professor)
---------------------
  python experimento.py A B C --sementes-arquivo sementes_ocultas.txt
  python experimento.py A B C --semente-base <valor secreto>
"""

import argparse
import sys

from agentes import REGISTRO
from wumpus import (carregar_agente, formatar_desfechos, formatar_tabela,
                    ler_sementes, resumir, rodar_experimento, salvar_csv,
                    sementes_publicas)


def main() -> int:
    p = argparse.ArgumentParser(description="Experimento do Mundo Wumpus (A × B × C)")
    p.add_argument("agentes", nargs="*", default=["A", "B", "C"],
                   help=f"atalhos {list(REGISTRO)} ou modulo:Classe (padrão: A B C)")
    p.add_argument("-n", "--mundos", type=int, default=200, help="quantidade de mundos (padrão 200)")
    p.add_argument("--semente-base", type=int, default=0, help="primeira semente (padrão 0)")
    p.add_argument("--sementes-arquivo", help="arquivo com uma semente por linha (substitui -n/--semente-base)")
    p.add_argument("--limite-acoes", type=int, default=250, help="ações máximas por partida (padrão 250)")
    p.add_argument("--limite-tempo", type=float, default=None, help="segundos máximos por partida")
    p.add_argument("--sem-posicao", action="store_true",
                   help="não entrega posição/direção na percepção (agente deve rastreá-las)")
    p.add_argument("--csv", help="salva o resultado de cada partida neste arquivo")
    p.add_argument("--silencioso", action="store_true", help="não mostra o progresso")
    args = p.parse_args()

    if args.sementes_arquivo:
        sementes = ler_sementes(args.sementes_arquivo)
        origem = f"arquivo {args.sementes_arquivo}"
    else:
        sementes = sementes_publicas(args.mundos, args.semente_base)
        origem = f"sementes {sementes[0]}..{sementes[-1]}"

    agentes = {}
    for spec in args.agentes:
        cls = carregar_agente(spec, REGISTRO)
        nome = cls.nome
        while nome in agentes:  # evita colisão de nomes iguais
            nome += "*"
        agentes[nome] = cls

    print(f"Mundo Wumpus · {len(sementes)} mundos ({origem}) · {len(agentes)} agente(s)\n",
          file=sys.stderr)
    resultados = rodar_experimento(
        agentes, sementes, progresso=not args.silencioso,
        limite_acoes=args.limite_acoes, limite_tempo_s=args.limite_tempo,
        fornecer_posicao=not args.sem_posicao,
    )

    resumo = resumir(resultados)
    print("\n## Resultado\n")
    print(formatar_tabela(resumo))
    print("\n## Desfechos (nº de mundos)\n")
    print(formatar_desfechos(resumo))

    # Mostra o primeiro erro de cada agente, para facilitar a depuração
    ja_mostrado = set()
    for r in resultados:
        if r.erro and r.agente not in ja_mostrado:
            ja_mostrado.add(r.agente)
            print(f"\n[!] Primeiro erro de '{r.agente}' (semente {r.semente}):\n{r.erro}",
                  file=sys.stderr)

    if args.csv:
        salvar_csv(resultados, args.csv)
        print(f"\nPartidas salvas em {args.csv}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
