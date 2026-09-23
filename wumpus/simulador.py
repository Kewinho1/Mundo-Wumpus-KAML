"""Execução de episódios e do experimento comparativo (A × B × C)."""

from __future__ import annotations

import csv
import importlib
import statistics
import sys
import time
import traceback
from collections import Counter
from dataclasses import asdict, dataclass
from typing import Callable, Iterable, Optional

from .acoes import Acao
from .agente import Agente
from .ambiente import Desfecho, MundoWumpus


@dataclass
class ResultadoEpisodio:
    agente: str
    semente: Optional[int]
    pontuacao: int
    desfecho: str
    acoes: int
    tempo_s: float
    erro: Optional[str] = None

    @property
    def sucesso(self) -> bool:
        return self.desfecho == Desfecho.SAIU_COM_OURO

    @property
    def morte(self) -> bool:
        return self.desfecho in Desfecho.MORTES


def rodar_episodio(
    fabrica: Callable[[], Agente],
    semente: Optional[int] = None,
    mundo: Optional[MundoWumpus] = None,
    *,
    limite_acoes: int = 250,
    limite_tempo_s: Optional[float] = None,
    fornecer_posicao: bool = True,
    observador: Optional[Callable] = None,
    nome: Optional[str] = None,
) -> ResultadoEpisodio:
    """Roda uma partida completa.

    fabrica   - a classe do agente (ou qualquer função sem argumentos que crie um)
    semente   - gera o mundo com MundoWumpus.gerar(semente); ou passe `mundo` pronto
    observador(mundo, acao, percepcao, agente) - chamado após cada ação (visualização)

    Se o agente lançar exceção ou devolver algo que não é Acao, a partida termina
    como ERRO_AGENTE com a mesma penalidade de uma morte (-1000).
    """
    if mundo is None:
        if semente is None:
            raise ValueError("Informe `semente` ou `mundo`")
        mundo = MundoWumpus.gerar(semente, limite_acoes=limite_acoes,
                                  fornecer_posicao=fornecer_posicao)
    nome = nome or getattr(fabrica, "nome", None) or getattr(fabrica, "__name__", "agente")

    erro = None
    inicio = time.perf_counter()
    try:
        agente = fabrica()
        percepcao = mundo.percepcao()
        while not mundo.terminado:
            acao = agente.agir(percepcao)
            if not isinstance(acao, Acao):
                raise TypeError(f"agir() deve devolver um membro de Acao, devolveu {acao!r}")
            percepcao = mundo.executar(acao)
            if observador is not None:
                observador(mundo, acao, percepcao, agente)
            if (limite_tempo_s is not None and not mundo.terminado
                    and time.perf_counter() - inicio > limite_tempo_s):
                mundo.encerrar(Desfecho.LIMITE_TEMPO)
    except Exception:
        erro = traceback.format_exc()
        mundo.encerrar(Desfecho.ERRO_AGENTE, MundoWumpus.PENALIDADE_MORTE)
    tempo = time.perf_counter() - inicio

    return ResultadoEpisodio(
        agente=nome,
        semente=mundo.semente if semente is None else semente,
        pontuacao=mundo.pontuacao,
        desfecho=mundo.desfecho,
        acoes=mundo.acoes,
        tempo_s=tempo,
        erro=erro,
    )


def rodar_experimento(
    agentes: dict,
    sementes: Iterable[int],
    progresso: bool = True,
    **kwargs,
) -> list:
    """Roda cada agente em TODOS os mundos da lista de sementes (mesmos mundos para todos).

    agentes - {"nome": ClasseDoAgente, ...}
    kwargs  - repassados para rodar_episodio (limite_acoes, limite_tempo_s, ...)
    """
    sementes = list(sementes)
    resultados = []
    for nome, fabrica in agentes.items():
        inicio = time.perf_counter()
        for i, semente in enumerate(sementes, 1):
            resultados.append(rodar_episodio(fabrica, semente, nome=nome, **kwargs))
            if progresso and (i % 20 == 0 or i == len(sementes)):
                print(f"\r  {nome}: {i}/{len(sementes)} mundos", end="", file=sys.stderr)
        if progresso:
            print(f"  ({time.perf_counter() - inicio:.1f}s)", file=sys.stderr)
    return resultados


# --------------------------------------------------------------------------
# Estatísticas e relatórios
# --------------------------------------------------------------------------

def resumir(resultados: Iterable[ResultadoEpisodio]) -> list:
    grupos: dict = {}
    for r in resultados:
        grupos.setdefault(r.agente, []).append(r)

    resumo = []
    for nome, rs in grupos.items():
        n = len(rs)
        pontos = [r.pontuacao for r in rs]
        resumo.append({
            "agente": nome,
            "mundos": n,
            "pontuacao_media": statistics.mean(pontos),
            "pontuacao_dp": statistics.stdev(pontos) if n > 1 else 0.0,
            "taxa_sucesso": sum(r.sucesso for r in rs) / n,
            "taxa_morte": sum(r.morte for r in rs) / n,
            "acoes_media": statistics.mean(r.acoes for r in rs),
            "tempo_medio_ms": statistics.mean(r.tempo_s for r in rs) * 1000,
            "erros": sum(1 for r in rs if r.erro),
            "desfechos": Counter(r.desfecho for r in rs),
        })
    return resumo


def _num(valor: float, casas: int = 1) -> str:
    return f"{valor:.{casas}f}".replace(".", ",")


def _pct(valor: float) -> str:
    return _num(valor * 100) + "%"


def formatar_tabela(resumo: list) -> str:
    """Tabela em Markdown no formato pedido no relatório."""
    linhas = [
        "| Agente | Pontuação (média ± dp) | Sucesso | Morte | Ações (média) | Tempo/partida | Erros |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for s in resumo:
        linhas.append(
            f"| {s['agente']} | {_num(s['pontuacao_media'])} ± {_num(s['pontuacao_dp'])} "
            f"| {_pct(s['taxa_sucesso'])} | {_pct(s['taxa_morte'])} "
            f"| {_num(s['acoes_media'])} | {_num(s['tempo_medio_ms'], 2)} ms | {s['erros']} |"
        )
    return "\n".join(linhas)


def formatar_desfechos(resumo: list) -> str:
    """Quantos mundos terminaram de cada forma, por agente."""
    colunas = [d for d in Desfecho.TODOS if any(s["desfechos"].get(d) for s in resumo)]
    linhas = ["| Agente | " + " | ".join(colunas) + " |",
              "|---|" + "---:|" * len(colunas)]
    for s in resumo:
        linhas.append(f"| {s['agente']} | " +
                      " | ".join(str(s["desfechos"].get(d, 0)) for d in colunas) + " |")
    return "\n".join(linhas)


def salvar_csv(resultados: Iterable[ResultadoEpisodio], caminho: str) -> None:
    """Um registro por partida — use para gráficos e para achar os mundos difíceis."""
    campos = ["agente", "semente", "pontuacao", "desfecho", "acoes", "tempo_s", "erro"]
    with open(caminho, "w", newline="", encoding="utf-8") as f:
        escritor = csv.DictWriter(f, fieldnames=campos)
        escritor.writeheader()
        for r in resultados:
            linha = asdict(r)
            linha["erro"] = (r.erro or "").strip().splitlines()[-1] if r.erro else ""
            escritor.writerow(linha)


# --------------------------------------------------------------------------
# Carregamento de agentes e sementes
# --------------------------------------------------------------------------

def carregar_agente(especificacao: str, registro: Optional[dict] = None) -> type:
    """'B' (atalho do registro) ou 'pacote.modulo:Classe' -> classe do agente."""
    alvo = (registro or {}).get(especificacao, especificacao)
    if ":" not in alvo:
        raise ValueError(f"'{especificacao}': use um atalho do registro ou o formato modulo:Classe")
    modulo, classe = alvo.split(":", 1)
    cls = getattr(importlib.import_module(modulo), classe)
    if not (isinstance(cls, type) and issubclass(cls, Agente)):
        raise TypeError(f"{alvo} não é uma subclasse de wumpus.Agente")
    return cls


def sementes_publicas(n: int = 200, base: int = 0) -> list:
    """Sementes de DESENVOLVIMENTO. A avaliação usa outras, ocultas."""
    return list(range(base, base + n))


def ler_sementes(caminho: str) -> list:
    """Um inteiro por linha; linhas vazias e comentários (#) são ignorados."""
    sementes = []
    with open(caminho, encoding="utf-8") as f:
        for linha in f:
            linha = linha.split("#", 1)[0].strip()
            if linha:
                sementes.append(int(linha))
    return sementes
