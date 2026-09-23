# Mundo Wumpus · Primeira Avaliação de IA (UniAnchieta)

Simulador oficial e classe base do trabalho. **Não altere nada dentro de `wumpus/`**: na avaliação, o professor roda os agentes do grupo com a versão original deste pacote e com sementes ocultas. O trabalho do grupo fica todo em `agentes/` (e em `tests/`, se quiserem).

Requisitos: Python 3.9 ou superior. Só a biblioteca padrão, nada para instalar.

## Estrutura

```
wumpus/                  ← simulador (NÃO EDITAR)
  acoes.py               Acao e Direcao
  percepcao.py           Percepcao (os 5 sensores)
  ambiente.py            MundoWumpus, vizinhos(), acoes_para_vizinho()
  agente.py              classe base Agente → agir(percepcao) -> Acao
  simulador.py           rodar_episodio(), rodar_experimento(), estatísticas
agentes/                 ← CÓDIGO DO GRUPO
  agente_aleatorio.py    exemplo pronto (piso de comparação)
  agente_reativo.py      Agente A  (esqueleto)
  agente_logico.py       Agente B  (esqueleto)
  agente_objetivo.py     Agente C  (esqueleto)
  __init__.py            REGISTRO de atalhos (A, B, C, ...)
experimento.py           tabela comparativa em N mundos
jogar.py                 jogar pelo teclado ou assistir um agente passo a passo
tests/test_ambiente.py   testes do simulador
```

## Primeiros passos

```bash
python -m unittest discover -s tests -v       # o simulador funciona?
python jogar.py --humano                      # sinta o ambiente jogando você mesmo
python jogar.py --agente aleatorio --classico # assista o agente de exemplo
python experimento.py aleatorio               # experimento com o agente de exemplo
```

## A interface (o que todo agente precisa respeitar)

```python
from wumpus import Agente, Acao, Percepcao

class MeuAgente(Agente):
    nome = "Meu agente"

    def agir(self, percepcao: Percepcao) -> Acao:
        if percepcao.brilho:
            return Acao.AGARRAR
        ...
```

1. Herde de `Agente` e implemente `agir(percepcao) -> Acao`.
2. O construtor não recebe argumentos. **Uma instância nova é criada para cada mundo**; a memória do agente vale só para aquela partida.
3. O agente só conhece o mundo pela `Percepcao`. Ler o estado do simulador (posição do Wumpus, poços, ouro) é fraude.
4. Exceção ou retorno que não seja `Acao` encerra a partida como `erro_do_agente`, com −1000.
5. Opcional: `depurar()` devolve um texto com o estado interno, mostrado pelo `jogar.py`.

### Percepção

| Campo | Sigla | Verdadeiro quando |
|---|---|---|
| `fedor` | FD | o Wumpus está na casa atual ou numa vizinha (N, S, L, O) |
| `brisa` | BR | há poço numa casa vizinha |
| `brilho` | BL | o ouro está na casa atual |
| `baque` | BQ | o último `AVANCAR` bateu na parede |
| `grito` | GR | o último `ATIRAR` matou o Wumpus |
| `posicao` | | `(x, y)` atual; `(1,1)` é o canto inferior esquerdo |
| `direcao` | | `Direcao.NORTE`, `LESTE`, `SUL` ou `OESTE` |

`posicao` e `direcao` são uma simplificação didática. Com `--sem-posicao` elas chegam como `None` e o agente precisa rastreá-las pelas próprias ações.

### Ações e pontuação

| Ação | Efeito |
|---|---|
| `AVANCAR` | anda uma casa para a frente (baque se for parede) |
| `VIRAR_ESQUERDA` / `VIRAR_DIREITA` | gira 90° |
| `AGARRAR` | pega o ouro, se estiver na casa |
| `ATIRAR` | a única flecha voa em linha reta; mata o Wumpus se ele estiver no caminho |
| `SAIR` | sai da caverna; só funciona em (1,1) |

+1000 ao sair em (1,1) com o ouro · −1000 ao morrer · −1 por ação · −10 adicional pela flecha. A partida também termina após 250 ações.

### O ambiente

Grade 4×4, agente em (1,1) virado para o leste, 1 Wumpus, 1 ouro e poço em cada casa (exceto a inicial) com probabilidade 0,2. Como no Russell & Norvig, o ouro pode estar numa casa com poço ou com o Wumpus, então **alguns mundos não têm solução segura**. Identificar esses mundos faz parte da análise.

### Funções auxiliares liberadas

- `vizinhos(pos)`: casas adjacentes dentro da grade.
- `acoes_para_vizinho(origem, direcao, destino)`: giros + `AVANCAR` para ir a uma casa adjacente. Ajuda a transformar o caminho da BFS em ações. A BFS é do grupo.

## Experimento

```bash
python experimento.py A B C                      # 200 mundos, sementes públicas 0..199
python experimento.py A B C --csv resultados.csv # uma linha por partida
python experimento.py A B C --semente-base 1000  # outro conjunto de mundos
python experimento.py agentes.meu_agente:MeuAgente -n 50
```

A saída já vem no formato da tabela do relatório: pontuação média ± desvio-padrão, taxa de sucesso, taxa de morte, ações médias, tempo por partida e contagem de desfechos. Use o CSV para descobrir **quais mundos derrotam cada agente**, e depois `python jogar.py --agente B --semente <n>` para assistir a derrota.

**Sementes ocultas.** As sementes 0..199 servem para desenvolvimento. No dia da avaliação, o professor roda todos os agentes em outro conjunto, desconhecido pelos grupos, que funciona como conjunto de teste (Aula 5). Agente ajustado para as sementes públicas não vai se sair bem.

## Regras que valem nota

- **Agente A**: sem memória. Nada guardado em `self` entre chamadas.
- **Agente B**: axiomas gerados por código; percepções entram só por `tell()`; segurança decidida só por `ask()` com **resolução por refutação**. Nada de `if brisa: evitar` escondido.
- **Sem bibliotecas de lógica no núcleo**: `sympy`, `pysat` e `z3` só em testes, para conferir resultados. CNF e resolução são implementadas pelo grupo.
- **Git obrigatório**: o histórico de commits mostra a contribuição de cada integrante.
- **IA generativa**: permitida, com declaração no relatório.

Dica para o Agente B: instancie as regras de brisa e fedor só das casas já visitadas e guarde em cache as respostas de `ask()`. Testem a BC separadamente em `tests/test_logica.py` antes de ligá-la ao agente (o mundo `MundoWumpus.classico()` reproduz o exemplo do livro).
