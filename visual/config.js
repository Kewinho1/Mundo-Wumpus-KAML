/* ==========================================================================
 *  CONFIGURAÇÃO VISUAL DO JOGO  ←  TROQUE AS IMAGENS AQUI
 * ==========================================================================
 *
 *  1. Coloque o arquivo da imagem na pasta  visual/imagens/
 *     (PNG, JPG, GIF animado, WEBP ou SVG — PNG com fundo transparente fica melhor).
 *  2. Troque o caminho correspondente abaixo. Ex.: agente: "imagens/meu_heroi.png"
 *  3. Recarregue a página no navegador (F5). Não precisa reiniciar o Python.
 *
 *  Os caminhos são relativos à pasta visual/.
 *  Se uma imagem não for encontrada, o jogo mostra o emoji de "reservas".
 *  Deixe null nas imagens opcionais para usar o comportamento padrão.
 */
window.CONFIG_VISUAL = {
  imagens: {
    // ----- Personagem -----------------------------------------------------
    agente: "imagens/agente.png",

    // Opcional: uma imagem para cada direção. Se preencher, ela é usada no
    // lugar da imagem "agente" (e o modoDirecao abaixo é ignorado).
    agentePorDirecao: {
      NORTE: null, // ex.: "imagens/heroi_costas.png"
      LESTE: null, // ex.: "imagens/heroi_direita.png"
      SUL: null,   // ex.: "imagens/heroi_frente.png"
      OESTE: null, // ex.: "imagens/heroi_esquerda.png"
    },

    agenteAndando: null, // opcional: mostrada enquanto anda (um GIF de caminhada fica ótimo)
    agenteComOuro: null, // opcional: depois de pegar o ouro
    agenteMorto: null,   // opcional: quando morre

    // ----- Monstro --------------------------------------------------------
    wumpus: "imagens/wumpus.png",
    wumpusMorto: null, // opcional: null = usa a imagem do wumpus, cinza e caída

    // ----- Cenário --------------------------------------------------------
    ouro: "imagens/ouro.webp",
    poco: "imagens/poco.gif",
    flecha: "imagens/flecha.svg", // desenhe a flecha apontando para a DIREITA
    chao: "imagens/chao.png",     // textura de fundo de cada casa
  },

  // Como o personagem mostra para onde está virado (quando há uma imagem só):
  //   "espelhar" – vira a imagem para a esquerda/direita (bom para personagem de lado)
  //   "girar"    – gira a imagem inteira 90° a cada giro (bom para visão de cima)
  //   "nenhum"   – não mexe na imagem
  // Em todos os modos aparece uma setinha dourada indicando a direção.
  modoDirecao: "espelhar",

  // Para que lado olha a imagem original do personagem: "direita" ou "esquerda".
  agenteOlhaPara: "direita",

  // Tamanho de cada figura como fração da casa (1 = casa inteira).
  tamanhos: { agente: 0.72, wumpus: 0.82, ouro: 0.5, poco: 0.9, flecha: 0.6 },

  // Duração das animações em milissegundos (o controle de velocidade da tela multiplica esses valores).
  velocidade: { movimento: 380, giro: 220, flecha: 420, pausaAgente: 450 },

  // Emojis usados se a imagem não carregar.
  reservas: { agente: "🧍", wumpus: "👹", ouro: "💰", poco: "🕳️", flecha: "➵" },
};
