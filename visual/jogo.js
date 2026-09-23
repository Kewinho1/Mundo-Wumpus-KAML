/* Interface visual do Mundo Wumpus.
 * Toda a regra do jogo roda no Python (wumpus/); aqui só desenhamos e animamos.
 * Para trocar imagens, edite config.js (não precisa mexer neste arquivo).
 */
"use strict";
(() => {
  const C = window.CONFIG_VISUAL || {};
  const IMG = C.imagens || {};
  const RESERVA = C.reservas || {};
  const $ = (s) => document.querySelector(s);

  const ANG = { LESTE: 0, SUL: 90, OESTE: 180, NORTE: 270 };
  const DELTA = { NORTE: [0, 1], LESTE: [1, 0], SUL: [0, -1], OESTE: [-1, 0] };
  const FATORES = [2, 1.4, 1, 0.6, 0.3]; // posições do controle de velocidade
  const NOMES_ACAO = {
    avancar: "avançar", virar_esquerda: "virar ↺", virar_direita: "virar ↻",
    agarrar: "agarrar", atirar: "atirar", sair: "sair", erro: "erro do agente",
  };
  const MORTES = ["caiu_no_poco", "devorado_pelo_wumpus"];

  let estado = null;
  let n = 4;          // tamanho da grade
  let S = 100;        // pixels por casa
  let casas = {};     // "x,y" -> { casa, itens, sens, x, y, assinatura }
  let el = {};        // agente, ator, corpo, giroSeta, flecha, flash
  let ultimoEvento = 0;
  let ocupado = false;
  let pendente = null;
  let auto = false;
  let loopAuto = 0;
  let geracao = 0;    // muda a cada novo jogo (cancela animações antigas)
  let anguloCorpo = 0, anguloSeta = 0, lado = 1, dirAtual = "LESTE";

  // ------------------------------------------------------------ utilidades

  const fator = () => FATORES[(+$("#velocidade").value || 3) - 1];
  const dur = (k) => Math.round(((C.velocidade || {})[k] ?? 300) * fator());
  const dormir = (ms) => new Promise((r) => setTimeout(r, ms));
  const chave = (c) => c[0] + "," + c[1];
  const px = (c) => [(c[0] - 1) * S, (n - c[1]) * S];
  const centro = (c) => { const [l, t] = px(c); return [l + S / 2, t + S / 2]; };
  const escapar = (t) => String(t).replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));

  function div(classe, texto) {
    const d = document.createElement("div");
    if (classe) d.className = classe;
    if (texto != null) d.textContent = texto;
    return d;
  }

  async function api(rota, dados) {
    const opcoes = dados === undefined ? {} : {
      method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(dados),
    };
    const r = await fetch("/api/" + rota, opcoes);
    const j = await r.json();
    if (!r.ok) throw new Error(j.erro || r.statusText);
    return j;
  }

  /** Coloca uma imagem dentro de `alvo`; se não carregar, mostra o emoji reserva. */
  function definirImagem(alvo, src, reserva) {
    const marca = (src || "") + "|" + reserva;
    if (alvo.dataset.marca === marca) return;
    alvo.dataset.marca = marca;
    const emoji = () => {
      const s = document.createElement("span");
      s.className = "emoji";
      s.textContent = reserva;
      alvo.replaceChildren(s);
    };
    if (!src) return emoji();
    const img = new Image();
    img.alt = "";
    img.draggable = false;
    img.onerror = () => {
      console.warn(`[Wumpus] Imagem não encontrada: visual/${src} — confira o nome do arquivo em config.js`);
      if (alvo.contains(img)) emoji();
    };
    img.src = src;
    alvo.replaceChildren(img);
  }

  function sprite(tipo, src) {
    const d = div("sprite");
    definirImagem(d, src === undefined ? IMG[tipo] : src, RESERVA[tipo] || "?");
    return d;
  }

  function reiniciarAnimacao(elemento, classe) {
    elemento.classList.remove(classe);
    void elemento.offsetWidth;
    elemento.classList.add(classe);
  }

  function tremer() { reiniciarAnimacao($("#tabuleiro"), "tremer"); }

  function piscar(cor) {
    el.flash.style.background = cor;
    reiniciarAnimacao(el.flash, "ativo");
  }

  function flutuar(texto, [x, y], cor) {
    const f = div("flutuante", texto);
    f.style.left = x + "px";
    f.style.top = y + "px";
    f.style.color = cor;
    f.addEventListener("animationend", () => f.remove());
    $("#tabuleiro").appendChild(f);
  }

  // ------------------------------------------------------------ tabuleiro

  function montar(tamanho) {
    n = tamanho;
    casas = {};
    const tab = $("#tabuleiro");
    tab.replaceChildren();
    for (const [k, v] of Object.entries(C.tamanhos || {})) tab.style.setProperty("--t-" + k, v);

    for (let y = n; y >= 1; y--) {
      for (let x = 1; x <= n; x++) {
        const casa = div("casa");
        if (x === 1 && y === 1) casa.classList.add("inicio");
        const chao = div("chao");
        if (IMG.chao) chao.style.backgroundImage = `url("${IMG.chao}")`;
        const itens = div("itens");
        const sens = div("sensacoes");
        casa.append(chao, div("coord", `${x},${y}`), itens, sens, div("nevoa", "?"));
        tab.appendChild(casa);
        casas[x + "," + y] = { casa, itens, sens, x, y, assinatura: "" };
      }
    }

    el.agente = div();
    el.agente.id = "agente";
    el.ator = div("ator");
    el.corpo = div("corpo sprite");
    el.giroSeta = div("giro-seta");
    el.giroSeta.appendChild(div("seta"));
    el.ator.append(el.corpo, el.giroSeta);
    el.agente.appendChild(el.ator);

    el.flecha = div();
    el.flecha.id = "flecha";
    el.flecha.hidden = true;
    el.flecha.appendChild(sprite("flecha"));

    el.flash = div();
    el.flash.id = "flash";
    tab.append(el.agente, el.flecha, el.flash);

    anguloCorpo = anguloSeta = 0;
    lado = 1;
    dirAtual = "LESTE";
    dimensionar();
  }

  function dimensionar() {
    const tab = $("#tabuleiro");
    const largura = Math.min($("#area").clientWidth, 760) - 24;
    const altura = window.innerHeight - 130;
    S = Math.max(48, Math.min(150, Math.floor(Math.min(largura, altura) / n)));
    tab.style.setProperty("--s", S + "px");
    tab.style.width = tab.style.height = n * S + "px";
    for (const c of Object.values(casas)) {
      const [l, t] = px([c.x, c.y]);
      c.casa.style.left = l + "px";
      c.casa.style.top = t + "px";
    }
    if (estado) posicionarAgente(estado.posicao, false);
  }

  function posicionarAgente(pos, animar, ms = dur("movimento")) {
    const [l, t] = px(pos);
    el.agente.style.transition = animar ? `transform ${ms}ms ease-in-out` : "none";
    el.agente.style.transform = `translate(${l}px, ${t}px)`;
  }

  /** Escolhe a imagem do personagem e vira ele para a direção atual. */
  function atualizarAgente(est, { animar = true, andando = false } = {}) {
    const dir = est.direcao;
    const morto = est.terminado && MORTES.includes(est.desfecho);
    const porDirecao = (IMG.agentePorDirecao || {})[dir];

    let src = IMG.agente;
    let usaPorDirecao = false;
    if (morto && IMG.agenteMorto) src = IMG.agenteMorto;
    else if (andando && IMG.agenteAndando) src = IMG.agenteAndando;
    else if (porDirecao) { src = porDirecao; usaPorDirecao = true; }
    else if (est.tem_ouro && IMG.agenteComOuro) src = IMG.agenteComOuro;
    definirImagem(el.corpo, src, RESERVA.agente || "🧍");

    const passo = (((ANG[dir] - ANG[dirAtual]) % 360) + 540) % 360 - 180;
    anguloSeta += passo;
    anguloCorpo += passo;
    if (dir === "LESTE") lado = 1;
    else if (dir === "OESTE") lado = -1;
    dirAtual = dir;

    const ms = animar ? dur("giro") : 0;
    el.giroSeta.style.transition = el.corpo.style.transition = `transform ${ms}ms ease-in-out`;
    el.giroSeta.style.transform = `rotate(${anguloSeta}deg)`;

    const inverte = C.agenteOlhaPara === "esquerda";
    let t = "none";
    if (!usaPorDirecao) {
      if (C.modoDirecao === "girar") t = `rotate(${anguloCorpo + (inverte ? 180 : 0)}deg)`;
      else if (C.modoDirecao !== "nenhum") t = `scaleX(${inverte ? -lado : lado})`;
    }
    el.corpo.style.transform = t;
  }

  function criarItem(tipo, junto) {
    const base = tipo === "wumpusMorto" ? "wumpus" : tipo;
    const d = div("item surgir " + base);
    d.addEventListener("animationend", (e) => {
      if (e.animationName === "surgir") d.classList.remove("surgir");
    });
    let src = IMG[base];
    if (tipo === "wumpus") d.classList.add("vivo");
    if (tipo === "wumpusMorto") {
      if (IMG.wumpusMorto) src = IMG.wumpusMorto;
      else d.classList.add("morto-padrao");
    }
    if (junto && base === "ouro") d.classList.add("junto");
    d.appendChild(sprite(base, src));
    return d;
  }

  // ------------------------------------------------------------ desenhar estado

  function renderizar(est) {
    const visitadas = new Set(est.visitadas.map(chave));
    const sensacoes = new Map(est.sensacoes.map((s) => [chave(s.casa), s]));
    const itensPor = {};
    const add = (c, tipo) => (itensPor[chave(c)] ||= []).push(tipo);
    est.pocos.forEach((c) => add(c, "poco"));
    if (est.wumpus) add(est.wumpus, est.wumpus_vivo ? "wumpus" : "wumpusMorto");
    if (est.ouro) add(est.ouro, "ouro");

    for (const [k, c] of Object.entries(casas)) {
      const visitada = visitadas.has(k);
      c.casa.classList.toggle("visivel", visitada || est.revelado);
      c.casa.classList.toggle("inexplorada", !visitada && est.revelado);

      const lista = itensPor[k] || [];
      const assinatura = lista.join("+");
      if (assinatura !== c.assinatura) {
        c.itens.replaceChildren(...lista.map((tipo) => criarItem(tipo, lista.length > 1)));
        c.assinatura = assinatura;
      }

      const s = sensacoes.get(k);
      const icones = s ? (s.brisa ? "💨" : "") + (s.fedor ? "🤢" : "") : "";
      if (c.sens.textContent !== icones) {
        c.sens.textContent = icones;
        c.sens.title = s ? [s.brisa && "brisa", s.fedor && "fedor"].filter(Boolean).join(" e ") : "";
      }
    }

    posicionarAgente(est.posicao, false);
    atualizarAgente(est);

    // painel
    const mundo = est.semente == null ? "clássico" : `semente ${est.semente}`;
    let quem = est.modo === "humano" ? "Você está jogando" : `Agente: <b>${escapar(est.nome)}</b>`;
    quem += ` · mundo ${mundo}`;
    if (est.revelado || !est.wumpus_vivo) quem += ` · Wumpus ${est.wumpus_vivo ? "vivo" : "morto 💀"}`;
    $("#quem").innerHTML = quem;
    $("#h-pontos").textContent = est.pontuacao;
    $("#h-acoes").textContent = `${est.acoes} / ${est.limite_acoes}`;
    $("#h-flecha").textContent = est.tem_flecha ? "🏹 1" : "— 0";
    $("#h-ouro").textContent = est.tem_ouro ? "💰 sim" : "— não";

    for (const chip of document.querySelectorAll(".chip")) {
      chip.classList.toggle("ligado", !!est.percepcao[chip.dataset.p]);
    }
    $("#descricao").textContent = est.descricao;

    const humano = est.modo === "humano";
    $("#painel-humano").hidden = !humano;
    $("#painel-agente").hidden = humano;
    for (const b of document.querySelectorAll("#painel-humano button, #passo, #auto")) b.disabled = est.terminado;

    $("#bloco-depurar").hidden = !est.depurar;
    $("#depurar").textContent = est.depurar || "";
    $("#bloco-erro").hidden = !est.erro;
    $("#erro").textContent = est.erro || "";
  }

  function registrar(texto) {
    const log = $("#log");
    log.prepend(div(null, texto));
    while (log.children.length > 300) log.lastChild.remove();
  }

  function mostrarErro(msg) {
    $("#bloco-erro").hidden = false;
    $("#erro").textContent = msg;
  }

  // ------------------------------------------------------------ animações

  async function animarAntes(ev, ant, novo) {
    if (ev.acao === "avancar" && chave(ant.posicao) !== chave(novo.posicao)) {
      atualizarAgente(ant, { andando: true, animar: false });
      posicionarAgente(novo.posicao, true);
      await dormir(dur("movimento"));
    } else if (ev.acao === "avancar" && ev.baque) {
      const [dx, dy] = DELTA[ant.direcao];
      const k = S * 0.22;
      await el.ator.animate(
        [{ transform: "translate(0,0)" }, { transform: `translate(${dx * k}px, ${-dy * k}px)` }, { transform: "translate(0,0)" }],
        { duration: Math.max(160, dur("movimento") * 0.7), easing: "ease-out" },
      ).finished;
    } else if (ev.acao === "atirar" && ev.flecha) {
      await animarFlecha(ev.flecha, ant.direcao, novo.revelado);
    } else if (ev.acao === "agarrar" && ev.agarrou) {
      const ouro = casas[chave(ant.posicao)]?.itens.querySelector(".item.ouro");
      if (ouro) {
        await ouro.animate(
          [{ transform: "translate(-50%,-50%) scale(1)", opacity: 1 },
           { transform: "translate(-50%,-120%) scale(1.5)", opacity: 0 }],
          { duration: Math.max(200, 450 * fator()), easing: "ease-in", fill: "forwards" },
        ).finished;
      }
    }
  }

  async function animarFlecha(f, dir, revelado) {
    const [dx, dy] = DELTA[dir];
    let fim = f.ate;
    // Sem o mapa revelado, a flecha sempre voa até a parede (não entrega onde o Wumpus está).
    if (!revelado) {
      fim = [...f.de];
      while (fim[0] + dx >= 1 && fim[0] + dx <= n && fim[1] + dy >= 1 && fim[1] + dy <= n) {
        fim = [fim[0] + dx, fim[1] + dy];
      }
    }
    const [l0, t0] = px(f.de);
    let [l1, t1] = px(fim);
    const acertouAqui = revelado && f.acertou;
    if (!acertouAqui) { l1 += dx * S * 0.45; t1 -= dy * S * 0.45; } // até encostar na parede
    const casasVoo = Math.max(Math.abs(fim[0] - f.de[0]), Math.abs(fim[1] - f.de[1]));
    const a = ANG[dir];

    el.flecha.hidden = false;
    await el.flecha.animate(
      [{ transform: `translate(${l0}px, ${t0}px) rotate(${a}deg)`, opacity: 1 },
       { transform: `translate(${l1}px, ${t1}px) rotate(${a}deg)`, opacity: 1, offset: 0.9 },
       { transform: `translate(${l1}px, ${t1}px) rotate(${a}deg)`, opacity: acertouAqui ? 0 : 0.2 }],
      { duration: dur("flecha") * (0.5 + casasVoo * 0.5), easing: "linear" },
    ).finished;
    el.flecha.hidden = true;
  }

  async function animarDepois(ev, novo) {
    if (ev.baque) { flutuar("BAQUE!", centro(novo.posicao), "#f0a070"); tremer(); }
    if (ev.grito) {
      flutuar("AAARGH!", novo.wumpus ? centro(novo.wumpus) : [n * S / 2, n * S / 2], "#ff7a7a");
      piscar("#ff000055");
      tremer();
    } else if (ev.acao === "atirar" && ev.flecha) {
      flutuar("errou…", centro(novo.posicao), "#bbb");
    }
    if (ev.agarrou) flutuar("+ OURO!", centro(novo.posicao), "#ffd54a");

    if (novo.terminado) {
      const d = novo.desfecho;
      if (d === "caiu_no_poco") {
        el.agente.classList.add("caindo");
        flutuar("AAAAH!", centro(novo.posicao), "#ff9a8a");
      } else if (d === "devorado_pelo_wumpus") {
        if (!IMG.agenteMorto) el.agente.classList.add("devorado");
        piscar("#ff0000aa");
        tremer();
        flutuar("NHAC!", centro(novo.posicao), "#ff5a5a");
      } else if (d && d.startsWith("saiu")) {
        el.agente.classList.add("saindo");
      }
      await dormir(1000);
    }
  }

  async function aplicar(novo, g) {
    const ant = estado;
    const ev = novo.evento;
    const eventoNovo = ev && ev.numero !== ultimoEvento;
    if (eventoNovo) ultimoEvento = ev.numero;

    if (eventoNovo && ant) await animarAntes(ev, ant, novo);
    if (g !== geracao) return;
    estado = novo;
    renderizar(novo);

    if (eventoNovo) {
      registrar(ev.acao === "erro"
        ? "✖ erro do agente"
        : `#${ev.numero} ${NOMES_ACAO[ev.acao] || ev.acao} → ${novo.percepcao_texto}`);
      await animarDepois(ev, novo);
      if (g !== geracao) return;
      if (novo.terminado) {
        registrar(`FIM: ${novo.desfecho_texto} (${novo.pontuacao} pontos)`);
        mostrarFim(novo);
      }
    }
  }

  function mostrarFim(est) {
    $("#fim")?.remove();
    const vitoria = est.desfecho === "saiu_com_ouro";
    const derrota = MORTES.includes(est.desfecho) || est.desfecho === "erro_do_agente";
    const classe = vitoria ? "vitoria" : derrota ? "derrota" : "neutro";
    const morreu = MORTES.includes(est.desfecho);
    const titulo = vitoria ? "Vitória!" : morreu ? "Você morreu!" : derrota ? "Erro do agente" : "Fim da partida";

    const fim = div();
    fim.id = "fim";
    if (morreu) fim.classList.add("fim-morte");
    fim.innerHTML = `
      <div class="caixa">
        <h3 class="${classe}">${titulo}</h3>
        <div>${escapar(est.desfecho_texto)}</div>
        <div class="pontos ${classe}">${est.pontuacao} pontos</div>
        <div style="color:var(--suave);font-size:13px;margin:-8px 0 14px">${est.acoes} ações</div>
        <div class="botoes">
          <button data-f="repetir">Renascer (mesmo mundo)</button>
          <button data-f="proximo" class="primario">Próximo mundo</button>
          <button data-f="ver">Ver mapa</button>
        </div>
      </div>`;
    fim.addEventListener("click", (e) => {
      const f = e.target.closest("button")?.dataset.f;
      if (f === "repetir") novoJogo();
      else if (f === "proximo") {
        $("#classico").checked = false;
        $("#semente").value = (parseInt($("#semente").value, 10) || 0) + 1;
        novoJogo();
      } else if (f === "ver" || e.target === fim) fim.remove();
    });
    $("#moldura").appendChild(fim);
  }

  // ------------------------------------------------------------ jogadas

  async function executar(tarefa) {
    if (ocupado) return false;
    ocupado = true;
    const g = geracao;
    try {
      const novo = await tarefa();
      if (g === geracao) await aplicar(novo, g);
    } catch (e) {
      mostrarErro(e.message);
      auto = false;
      atualizarAuto();
    } finally {
      if (g === geracao) ocupado = false;
    }
    return true;
  }

  function acaoHumana(acao) {
    if (!estado || estado.modo !== "humano" || estado.terminado) return;
    if (ocupado) { pendente = acao; return; } // guarda a última tecla apertada durante a animação
    executar(() => api("acao", { acao })).then(() => {
      if (pendente) {
        const p = pendente;
        pendente = null;
        acaoHumana(p);
      }
    });
  }

  function passoAgente() {
    if (!estado || estado.modo !== "agente" || estado.terminado) return Promise.resolve();
    return executar(() => api("passo", {}));
  }

  function atualizarAuto() {
    $("#auto").innerHTML = auto ? "⏸ Pausar <kbd>P</kbd>" : "▶ Jogar sozinho <kbd>P</kbd>";
  }

  async function alternarAuto() {
    if (!estado || estado.modo !== "agente") return;
    auto = !auto;
    atualizarAuto();
    if (!auto) return;
    const id = ++loopAuto;
    while (auto && id === loopAuto && estado && !estado.terminado) {
      if (!ocupado) await passoAgente();
      await dormir(dur("pausaAgente"));
    }
    if (id === loopAuto) { auto = false; atualizarAuto(); }
  }

  function lerFormulario() {
    return {
      modo: $("#modo").value,
      semente: parseInt($("#semente").value, 10) || 0,
      classico: $("#classico").checked,
      nevoa: $("#nevoa").checked,
      sem_posicao: $("#sem_posicao").checked,
    };
  }

  async function novoJogo() {
    geracao++;
    auto = false;
    loopAuto++;
    pendente = null;
    ocupado = true;
    const g = geracao;
    atualizarAuto();
    try {
      const est = await api("novo", lerFormulario());
      if (g !== geracao) return;
      $("#fim")?.remove();
      $("#log").replaceChildren();
      montar(est.tamanho);
      estado = est;
      ultimoEvento = est.evento ? est.evento.numero : 0;
      renderizar(est);
      atualizarAgente(est, { animar: false });
      registrar(`Início → ${est.percepcao_texto}`);
      if (est.terminado) {
        registrar(`FIM: ${est.desfecho_texto}`);
        mostrarFim(est);
      }
    } catch (e) {
      mostrarErro(e.message);
    } finally {
      if (g === geracao) ocupado = false;
    }
  }

  // ------------------------------------------------------------ início

  function ligarControles() {
    $("#config").addEventListener("submit", (e) => { e.preventDefault(); novoJogo(); });
    $("#sortear").addEventListener("click", () => {
      $("#semente").value = Math.floor(Math.random() * 10000);
      $("#classico").checked = false;
      novoJogo();
    });
    $("#modo").addEventListener("change", () => {
      $("#rotulo-nevoa").hidden = $("#modo").value === "humano";
      novoJogo();
    });
    for (const b of document.querySelectorAll("#painel-humano button")) {
      b.addEventListener("click", () => { b.blur(); acaoHumana(b.dataset.acao); });
    }
    $("#passo").addEventListener("click", (e) => { e.currentTarget.blur(); passoAgente(); });
    $("#auto").addEventListener("click", (e) => { e.currentTarget.blur(); alternarAuto(); });
    window.addEventListener("resize", dimensionar);

    document.addEventListener("keydown", (e) => {
      if (e.ctrlKey || e.metaKey || e.altKey) return;
      if (e.target.matches?.("input[type=number], select")) return;
      const k = e.key.toLowerCase();
      if (k === "escape") { $("#fim")?.remove(); return; }
      if (k === "r") { e.preventDefault(); novoJogo(); return; }
      if (!estado) return;
      if (estado.modo === "humano") {
        const mapa = {
          w: "avancar", arrowup: "avancar",
          a: "virar_esquerda", arrowleft: "virar_esquerda",
          d: "virar_direita", arrowright: "virar_direita",
          g: "agarrar", f: "atirar", " ": "atirar", s: "sair",
        };
        if (mapa[k]) { e.preventDefault(); acaoHumana(mapa[k]); }
      } else if (k === " " || k === "enter" || k === "n") {
        e.preventDefault();
        passoAgente();
      } else if (k === "p") {
        e.preventDefault();
        alternarAuto();
      }
    });
  }

  async function iniciar() {
    // Pré-carrega as imagens para não piscar quando trocar (ex.: agenteAndando).
    const fontes = [...Object.values(IMG), ...Object.values(IMG.agentePorDirecao || {})];
    for (const src of fontes) if (typeof src === "string") new Image().src = src;

    ligarControles();
    try {
      const cfg = await api("config");
      const sel = $("#modo");
      sel.add(new Option("🧑 Você (humano)", "humano"));
      for (const a of cfg.agentes) sel.add(new Option(`🤖 Agente ${a}`, a));
      const p = cfg.padroes || {};
      if (p.modo && ![...sel.options].some((o) => o.value === p.modo)) sel.add(new Option(`🤖 ${p.modo}`, p.modo));
      sel.value = p.modo || "humano";
      $("#semente").value = p.semente ?? 0;
      $("#classico").checked = !!p.classico;
      $("#nevoa").checked = !!p.nevoa;
      $("#sem_posicao").checked = !!p.sem_posicao;
      $("#rotulo-nevoa").hidden = sel.value === "humano";
    } catch (e) {
      mostrarErro("Não consegui falar com o Python. Rode:  python jogar_visual.py\n\n" + e.message);
      return;
    }
    await novoJogo();
  }

  iniciar();
})();
