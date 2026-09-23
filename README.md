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

## Versão visual (navegador)

```bash
python jogar_visual.py                         # você joga; abre o navegador sozinho
python jogar_visual.py --agente B --classico   # assiste o agente B jogando
python jogar_visual.py --agente C --nevoa      # esconde o que o agente não visitou
```

Teclas: `W`/`↑` avançar · `A`/`←` e `D`/`→` virar · `G` agarrar · `F`/`Espaço` atirar · `S` sair · `R` reiniciar. Assistindo um agente: `Espaço` dá um passo, `P` liga/desliga o modo automático.

**Trocar as imagens:** coloque os arquivos em `visual/imagens/` e altere os caminhos em `visual/config.js` (personagem, Wumpus, ouro, poço, flecha, chão e imagens opcionais por direção, andando, com ouro e morto). Depois é só apertar F5 no navegador. A versão visual usa o simulador de `wumpus/` sem nenhuma alteração.

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


## Resultados do grupo

Todos os 30 testes passam (`python -m unittest discover -s tests`). Saída de `python experimento.py aleatorio A B C` com as sementes públicas 0..199:

| Agente | Pontuação (média ± dp) | Sucesso | Morte | Ações (média) | Tempo/partida |
|---|---:|---:|---:|---:|---:|
| Aleatório (exemplo) | −926,8 ± 361,3 | 3,5% | 95,0% | 11,8 | 0,03 ms |
| A · Reativo | −324,0 ± 522,6 | 2,5% | 34,0% | 9,0 | 0,02 ms |
| B · Lógico | 278,4 ± 450,2 | 29,0% | 0,0% | 11,6 | 0,75 ms |
| C · Lógico + BFS | 359,4 ± 480,2 | 37,5% | 0,0% | 13,4 | 1,30 ms |

| Agente | saiu com ouro | saiu sem ouro | caiu no poço | devorado pelo Wumpus |
|---|---:|---:|---:|---:|
| Aleatório (exemplo) | 7 | 3 | 133 | 57 |
| A · Reativo | 5 | 127 | 46 | 22 |
| B · Lógico | 58 | 142 | 0 | 0 |
| C · Lógico + BFS | 75 | 125 | 0 | 0 |

### Como cada agente funciona

- **A (reativo):** regras condição → ação avaliadas em ordem (agarrar se brilho; sair em (1,1) se há perigo ou com 15% de chance; virar ao bater ou, 70% das vezes, ao sentir brisa/fedor; senão avançar). Não guarda nada em `self`, e o gerador aleatório fica no módulo. Morre em 34% dos mundos porque não lembra onde sentiu perigo. Só sai com o ouro se passar por (1,1) por acaso, já que não sabe que o pegou.
- **B (lógico):** a cada casa nova, gera por código `¬P`, `¬W ∨ ¬WumpusVivo`, `B(x,y) ⇔ ∨P(vizinhos)` e `F(x,y) ⇔ ∨W(casa e vizinhos)` e passa a percepção por `tell()`. Uma casa é segura quando `ask(¬P)` e `ask(¬W ∨ ¬WumpusVivo)` são provados por resolução por refutação (conjunto de suporte, descarte de cláusulas subsumidas e só as cláusulas ligadas aos símbolos da consulta). As respostas "provado" ficam em cache porque a BC é monotônica. Explora por DFS com retrocesso e, com o ouro, desempilha até (1,1).
- **C (lógico + objetivo):** usa a mesma BC e as mesmas perguntas do B, mas planeja com BFS até a casa segura mais próxima da fronteira e volta a (1,1) pelo menor caminho entre casas já visitadas. Diante do dilema do risco, **atira** se existe casa da fronteira provada sem poço, ou seja, cujo único risco é o Wumpus. Com grito, o Wumpus morre. Sem grito, a BC aprende `¬W` na linha da flecha. Se não há onde atirar, **volta e sai**, porque entrar numa casa incerta tem utilidade esperada negativa. A flecha é a diferença do C para o B: C resolve 7 dos 10 mundos em que o ouro está na casa do Wumpus, e B resolve 0.

### Mundos sem solução segura

Classificação das 200 sementes públicas feita com o estado real do mundo (só para análise, nunca dentro de um agente):

| Tipo de mundo | Mundos | Exemplos de semente | Saída com ouro (B / C) |
|---|---:|---|---:|
| Ouro dentro de um poço: impossível | 46 | 9, 16, 17, 20, 23 | 0 / 0 |
| Ouro cercado por poços: impossível | 11 | 4, 27, 44, 48, 83 | 0 / 0 |
| Ouro na casa do Wumpus: só com a flecha | 10 | 2, 13, 60, 67, 96 | 0 / 7 |
| Ouro alcançável sem passar por poço | 133 | 0, 1, 3, 5, 6 | 58 / 68 |

- **57 dos 200 mundos (28,5%) não têm solução nenhuma.** Nesses, o melhor possível é sair sem morrer, e B e C fazem isso em todos.
- O limite superior realista fica perto de **143 mundos (71,5%)**. C chega a 75, cerca de 52% desse teto.
- Nos 65 mundos alcançáveis em que C sai sem ouro, a BC não consegue provar nenhuma casa segura a mais. Chegar ao ouro exigiria arriscar, e C escolhe não arriscar porque um único −1000 custa mais que o ganho esperado. Por isso B e C têm 0% de morte.

Para assistir um caso: `python jogar.py --agente C --semente 60` (ouro com o Wumpus, resolvido com a flecha) ou `--semente 9` (ouro no poço).

