#!/usr/bin/env python3
"""Versão visual do Mundo Wumpus: abre o jogo no navegador.

Exemplos
--------
  python jogar_visual.py                          # você joga (abre o navegador)
  python jogar_visual.py --semente 7
  python jogar_visual.py --agente B --classico    # assiste o agente B
  python jogar_visual.py --agente C --nevoa       # esconde o que o agente não visitou
  python jogar_visual.py --porta 8080 --sem-navegador

Tudo pode ser trocado também pela própria página (modo, semente, névoa...).

Controles do modo humano (teclado ou botões da tela):
  W / ↑ avançar · A / ← virar à esquerda · D / → virar à direita
  G agarrar · F / Espaço atirar · S sair · R reiniciar

IMAGENS: ficam em visual/imagens/ e são escolhidas em visual/config.js.
Depois de trocar uma imagem, basta recarregar a página (F5).

Usa o simulador de wumpus/ sem nenhuma modificação e só a biblioteca padrão.
"""

import argparse
import json
import sys
import threading
import traceback
import webbrowser
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from agentes import REGISTRO
from wumpus import Acao, Desfecho, MundoWumpus, carregar_agente

PASTA_VISUAL = Path(__file__).resolve().parent / "visual"

TEXTOS_DESFECHO = {
    Desfecho.SAIU_COM_OURO: "Saiu da caverna com o ouro!",
    Desfecho.SAIU_SEM_OURO: "Saiu da caverna sem o ouro.",
    Desfecho.CAIU_NO_POCO: "Caiu num poço!",
    Desfecho.DEVORADO: "Foi devorado pelo Wumpus!",
    Desfecho.LIMITE_ACOES: "Limite de ações atingido.",
    Desfecho.LIMITE_TEMPO: "Limite de tempo atingido.",
    Desfecho.ERRO_AGENTE: "O agente deu erro.",
}


class ErroRequisicao(Exception):
    """Pedido inválido vindo da página (vira HTTP 400)."""


class Partida:
    """Um mundo + quem está jogando (humano ou agente) + o que a página precisa saber."""

    def __init__(self, modo: str, semente: int, classico: bool, nevoa: bool, sem_posicao: bool):
        opcoes = {"fornecer_posicao": not sem_posicao}
        self.mundo = MundoWumpus.classico(**opcoes) if classico else MundoWumpus.gerar(semente, **opcoes)
        self.humano = modo == "humano"
        self.revelar = not self.humano and not nevoa
        self.nome = "Humano"
        self.agente = None
        self.erro = None
        self.texto_fim = None
        self.evento = None
        self.sensacoes = {}
        self.percepcao = self.mundo.percepcao()
        self._anotar()

        if not self.humano:
            try:
                classe = carregar_agente(modo, REGISTRO)
                self.nome = getattr(classe, "nome", modo)
                self.agente = classe()
            except Exception:
                self._falhou()

    # ------------------------------------------------------------ jogadas

    def executar(self, acao: Acao) -> None:
        m = self.mundo
        if m.terminado:
            self.evento = None
            return
        origem = m.posicao
        flecha = {"de": list(origem), "ate": list(self._alvo_flecha())} \
            if acao is Acao.ATIRAR and m.tem_flecha else None
        tinha_ouro = m.tem_ouro

        self.percepcao = m.executar(acao)

        if flecha:
            flecha["acertou"] = self.percepcao.grito
        self.evento = {
            "numero": m.acoes,
            "acao": acao.value,
            "de": list(origem),
            "flecha": flecha,
            "baque": self.percepcao.baque,
            "grito": self.percepcao.grito,
            "agarrou": m.tem_ouro and not tinha_ouro,
        }
        self._anotar()

    def passo_agente(self) -> None:
        if self.agente is None or self.mundo.terminado:
            self.evento = None
            return
        try:
            acao = self.agente.agir(self.percepcao)
            if not isinstance(acao, Acao):
                raise TypeError(f"agir() deve devolver um membro de Acao, devolveu {acao!r}")
        except Exception:
            self._falhou()
            return
        self.executar(acao)

    def _falhou(self) -> None:
        """Mesma regra do simulador: erro do agente encerra a partida com -1000."""
        tipo, excecao, _ = sys.exc_info()
        self.erro = traceback.format_exc()
        if tipo is NotImplementedError:
            self.texto_fim = "Esse agente ainda não foi implementado (veja o quadro Erro ao lado)."
            self.erro = (
                f"O agente '{self.nome}' ainda não foi implementado "
                f"({excecao or 'NotImplementedError'}).\n\n"
                "Escreva o método agir() dele na pasta agentes/. Enquanto isso, "
                "escolha 'Agente aleatorio' em \"Quem joga\" para ver o modo automático "
                "funcionando.\n\n" + self.erro
            )
        self.mundo.encerrar(Desfecho.ERRO_AGENTE, MundoWumpus.PENALIDADE_MORTE)
        self.evento = {"numero": self.mundo.acoes + 0.5, "acao": "erro"}

    def _alvo_flecha(self) -> tuple:
        """Até onde a flecha voa: a casa do Wumpus vivo ou a última antes da parede."""
        m = self.mundo
        dx, dy = m.direcao.delta
        x, y = m.posicao
        while 1 <= x + dx <= m.tamanho and 1 <= y + dy <= m.tamanho:
            x, y = x + dx, y + dy
            if (x, y) == m.wumpus and m.wumpus_vivo:
                break
        return x, y

    def _anotar(self) -> None:
        """Guarda o que foi sentido em cada casa visitada (para desenhar no tabuleiro)."""
        self.sensacoes[self.mundo.posicao] = {
            "fedor": self.percepcao.fedor,
            "brisa": self.percepcao.brisa,
        }

    # ------------------------------------------------------------ para a página

    def estado(self) -> dict:
        m, p = self.mundo, self.percepcao
        revelar = self.revelar or m.terminado

        def visivel(casa) -> bool:
            return revelar or casa in m.visitadas

        depurar = ""
        if self.agente is not None:
            try:
                depurar = self.agente.depurar() or ""
            except Exception as e:
                depurar = f"(depurar() falhou: {e})"

        return {
            "modo": "humano" if self.humano else "agente",
            "nome": self.nome,
            "semente": m.semente,
            "tamanho": m.tamanho,
            "revelado": revelar,
            "posicao": list(m.posicao),
            "direcao": m.direcao.name,
            "visitadas": [list(c) for c in sorted(m.visitadas)],
            "wumpus": list(m.wumpus) if visivel(m.wumpus) else None,
            "wumpus_vivo": m.wumpus_vivo,
            "pocos": [list(c) for c in sorted(m.pocos) if visivel(c)],
            "ouro": list(m.ouro) if m.ouro_no_chao and visivel(m.ouro) else None,
            "tem_ouro": m.tem_ouro,
            "tem_flecha": m.tem_flecha,
            "pontuacao": m.pontuacao,
            "acoes": m.acoes,
            "limite_acoes": m.limite_acoes,
            "terminado": m.terminado,
            "desfecho": m.desfecho,
            "desfecho_texto": self.texto_fim or TEXTOS_DESFECHO.get(m.desfecho, m.desfecho or ""),
            "percepcao": {
                "fedor": p.fedor, "brisa": p.brisa, "brilho": p.brilho,
                "baque": p.baque, "grito": p.grito,
            },
            "percepcao_texto": str(p),
            "descricao": p.descricao(),
            "sensacoes": [{"casa": list(c), **s} for c, s in self.sensacoes.items()],
            "evento": self.evento,
            "depurar": depurar,
            "erro": self.erro,
        }


# --------------------------------------------------------------------------
# Servidor HTTP local (página em visual/ + API JSON em /api/)
# --------------------------------------------------------------------------

TRAVA = threading.Lock()
SESSAO = {"partida": None, "padroes": {}}


def rotear(metodo: str, rota: str, dados: dict) -> dict:
    partida = SESSAO["partida"]

    if rota == "/api/config":
        return {"agentes": list(REGISTRO), "padroes": SESSAO["padroes"]}

    if rota == "/api/novo" and metodo == "POST":
        try:
            semente = int(dados.get("semente", 0))
        except (TypeError, ValueError):
            raise ErroRequisicao("A semente precisa ser um número inteiro") from None
        partida = SESSAO["partida"] = Partida(
            modo=str(dados.get("modo") or "humano"),
            semente=semente,
            classico=bool(dados.get("classico")),
            nevoa=bool(dados.get("nevoa")),
            sem_posicao=bool(dados.get("sem_posicao")),
        )
        return partida.estado()

    if partida is None:
        raise ErroRequisicao("Nenhuma partida em andamento")

    if rota == "/api/estado":
        return partida.estado()

    if rota == "/api/acao" and metodo == "POST":
        if not partida.humano:
            raise ErroRequisicao("Quem está jogando é o agente")
        try:
            acao = Acao(dados.get("acao"))
        except ValueError:
            raise ErroRequisicao(f"Ação desconhecida: {dados.get('acao')!r}") from None
        partida.executar(acao)
        return partida.estado()

    if rota == "/api/passo" and metodo == "POST":
        if partida.humano:
            raise ErroRequisicao("Quem está jogando é você")
        partida.passo_agente()
        return partida.estado()

    raise ErroRequisicao(f"Rota desconhecida: {metodo} {rota}")


class Servidor(SimpleHTTPRequestHandler):
    # O Windows nem sempre conhece esses tipos; sem eles o navegador pode recusar a imagem.
    extensions_map = {
        **SimpleHTTPRequestHandler.extensions_map,
        ".webp": "image/webp",
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".gif": "image/gif",
        ".svg": "image/svg+xml",
        ".avif": "image/avif",
        ".js": "text/javascript",
        ".css": "text/css",
        ".woff2": "font/woff2",
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(PASTA_VISUAL), **kwargs)

    def end_headers(self):
        # Sem cache: trocou a imagem, apertou F5, já aparece.
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def log_message(self, *args):
        pass

    def do_GET(self):
        if self.path.startswith("/api/"):
            self._api("GET")
        else:
            super().do_GET()

    def do_POST(self):
        self._api("POST")

    def _api(self, metodo: str) -> None:
        rota = self.path.split("?", 1)[0]
        codigo = 200
        try:
            tamanho = int(self.headers.get("Content-Length") or 0)
            dados = json.loads(self.rfile.read(tamanho) or b"{}") if tamanho else {}
            with TRAVA:
                resposta = rotear(metodo, rota, dados)
        except ErroRequisicao as e:
            codigo, resposta = 400, {"erro": str(e)}
        except Exception:
            traceback.print_exc()
            codigo, resposta = 500, {"erro": traceback.format_exc()}

        corpo = json.dumps(resposta).encode("utf-8")
        self.send_response(codigo)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(corpo)))
        self.end_headers()
        self.wfile.write(corpo)


def main() -> int:
    p = argparse.ArgumentParser(description="Mundo Wumpus no navegador")
    quem = p.add_mutually_exclusive_group()
    quem.add_argument("--humano", action="store_true", help="você joga (padrão)")
    quem.add_argument("--agente", help=f"atalho {list(REGISTRO)} ou modulo:Classe")
    p.add_argument("--semente", type=int, default=0, help="semente do mundo (padrão 0)")
    p.add_argument("--classico", action="store_true", help="usa o mundo da figura 7.2 do livro")
    p.add_argument("--nevoa", action="store_true",
                   help="ao assistir um agente, esconde o que ele não visitou")
    p.add_argument("--sem-posicao", action="store_true", help="percepção sem posição/direção")
    p.add_argument("--porta", type=int, default=8000, help="porta do servidor local (padrão 8000)")
    p.add_argument("--sem-navegador", action="store_true", help="não abre o navegador sozinho")
    args = p.parse_args()

    SESSAO["padroes"] = {
        "modo": args.agente or "humano",
        "semente": args.semente,
        "classico": args.classico,
        "nevoa": args.nevoa,
        "sem_posicao": args.sem_posicao,
    }

    servidor = None
    for porta in range(args.porta, args.porta + 20):
        try:
            servidor = ThreadingHTTPServer(("127.0.0.1", porta), Servidor)
            break
        except OSError:
            continue
    if servidor is None:
        print(f"Nenhuma porta livre entre {args.porta} e {args.porta + 19}.", file=sys.stderr)
        return 1

    url = f"http://127.0.0.1:{servidor.server_port}/"
    print(f"Mundo Wumpus visual rodando em {url}")
    print("Feche com Ctrl+C.")
    if not args.sem_navegador:
        webbrowser.open(url)
    try:
        servidor.serve_forever()
    except KeyboardInterrupt:
        print("\nServidor encerrado.")
    finally:
        servidor.server_close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
