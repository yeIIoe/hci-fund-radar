/* HCI MACRO DIRECTION — MÓDULO DE MERCADO (ui_mercado.js)
 *
 * O painel mostrava bancos centrais, sentimento e calendário, mas quase nada do que o MERCADO
 * está precificando. Este módulo entrega a faixa de mercado (DXY, petróleo, ouro, S&P, Nasdaq,
 * juro de 2 e 10 anos), a tabela de juros por moeda, o diferencial de juros por par, a
 * probabilidade da próxima decisão de cada banco central e a reação do câmbio após o último
 * dado relevante.
 *
 * REGRAS DA CASA que este arquivo respeita:
 *   - Yields e precificação NUNCA entram no cálculo do sentimento. Aqui eles são apenas DADO
 *     DE MERCADO exibido e coluna de comparação (Leitura HCI × Mercado precifica × Diferença).
 *   - Quando não há fonte para um número, o campo vem null e a tela escreve "sem fonte".
 *     Nunca se inventa, nunca se estima sem rótulo.
 *   - Cores: verde só para ALTA de juro, vermelho só para CORTE/risco, turquesa para seleção.
 *     Índices e commodities usam verde sobe / vermelho cai (pedido explícito da revisão);
 *     juros de mercado ficam em cor neutra.
 *
 * INTERFACE (window.HCI_MERCADO) — chamada de dentro de ui_macro.js por outro módulo:
 *   carrega()                       Promise<void>; lê data/mercado.json e data/precificacao.json
 *   pronto()                        boolean
 *   faixaHtml()                     string — a faixa de mercado do topo da aba
 *   precificacaoDe(moeda, leitura)  {texto, direcao, classe, diff, diffClasse, fonte, qualidade, titulo}
 *   reacaoHtml()                    string — bloco "Reação após o {evento}" ("" quando não há)
 *
 * Nenhuma função lança exceção: se o JSON faltar, a saída explica que o coletor ainda não rodou.
 */
(function () {
  "use strict";

  const raiz = typeof window !== "undefined" ? window : globalThis;

  const MOEDAS = ["USD", "EUR", "GBP", "JPY", "AUD", "NZD", "CAD", "CHF"];
  const BANDEIRA = {
    USD: "🇺🇸", EUR: "🇪🇺", GBP: "🇬🇧", JPY: "🇯🇵",
    AUD: "🇦🇺", NZD: "🇳🇿", CAD: "🇨🇦", CHF: "🇨🇭",
  };
  const NOME_BANCO = {
    USD: "Fed", EUR: "BCE", GBP: "BoE", JPY: "BoJ",
    AUD: "RBA", NZD: "RBNZ", CAD: "BoC", CHF: "SNB",
  };
  // Ordem e rótulo dos cartões da faixa. Juros são "bp" e cor neutra; o resto é "%".
  const CARTOES = [
    { chave: "DXY",    rotulo: "DXY",             tipo: "pct",  casas: 2 },
    { chave: "WTI",    rotulo: "Petróleo WTI",    tipo: "pct",  casas: 2, prefixo: "US$ " },
    { chave: "OURO",   rotulo: "Ouro",            tipo: "pct",  casas: 1, prefixo: "US$ " },
    { chave: "SP500",  rotulo: "S&P 500",         tipo: "pct",  casas: 0 },
    { chave: "NASDAQ", rotulo: "Nasdaq",          tipo: "pct",  casas: 0 },
    { chave: "US2Y",   rotulo: "Juro EUA 2 anos",  tipo: "juro", casas: 2 },
    { chave: "US10Y",  rotulo: "Juro EUA 10 anos", tipo: "juro", casas: 2 },
  ];
  const DIRECAO_TXT = { alta: "alta", corte: "corte", manutencao: "manutenção" };
  // Escala hawkish→dovish usada na comparação Leitura HCI × Mercado.
  const GRAU = { alta: 2, manutencao: 1, corte: 0 };

  const SEM_DADOS = "sem dados ainda — o coletor roda no GitHub Actions";

  /* ------------------------------------------------------------------ utilidades ---- */

  const esc = (s) => String(s == null ? "" : s).replace(/[&<>"]/g,
    (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));

  const eNum = (v) => typeof v === "number" && isFinite(v);

  // Formata número em pt-BR (vírgula decimal, ponto de milhar), sem depender de ICU.
  function fmt(v, casas) {
    if (!eNum(v)) return null;
    const c = casas == null ? 2 : casas;
    const neg = v < 0;
    const s = Math.abs(v).toFixed(c);
    const partes = s.split(".");
    const comMilhar = partes[0].replace(/\B(?=(\d{3})+(?!\d))/g, ".");
    return (neg ? "−" : "") + comMilhar + (partes[1] ? "," + partes[1] : "");
  }

  // Variação com sinal explícito: "+0,42%" / "−3 bp" / "0,00%".
  function fmtVar(v, casas, sufixo) {
    if (!eNum(v)) return null;
    const corpo = fmt(Math.abs(v), casas);
    const sinal = v > 0 ? "+" : v < 0 ? "−" : "";
    return sinal + corpo + (sufixo || "");
  }

  // Classe de cor para variação: verde sobe, vermelho cai, neutro para juros e zero.
  function classeVar(v, tipo) {
    if (!eNum(v) || tipo === "juro" || v === 0) return "mkt-neutro";
    return v > 0 ? "mkt-sobe" : "mkt-cai";
  }

  function fmtPct100(p) {
    if (!eNum(p)) return null;
    return Math.round(p * 100) + "%";
  }

  function dataCurta(iso) {
    if (!iso || String(iso).length < 10) return null;
    const s = String(iso);
    return s.slice(8, 10) + "/" + s.slice(5, 7);
  }

  function horaUtc(iso) {
    if (!iso) return null;
    const d = new Date(iso);
    if (isNaN(d)) return null;
    const p = (n) => String(n).padStart(2, "0");
    return `${p(d.getUTCDate())}/${p(d.getUTCMonth() + 1)} ${p(d.getUTCHours())}:${p(d.getUTCMinutes())} UTC`;
  }

  // Dias de calendário até uma data AAAA-MM-DD, contados no fuso de Brasília (UTC−3).
  function diasAte(isoData) {
    if (!isoData || String(isoData).length < 10) return null;
    const s = String(isoData);
    const alvo = Date.UTC(+s.slice(0, 4), +s.slice(5, 7) - 1, +s.slice(8, 10));
    const agora = new Date(Date.now() - 3 * 3600e3);
    const hoje = Date.UTC(agora.getUTCFullYear(), agora.getUTCMonth(), agora.getUTCDate());
    if (isNaN(alvo) || isNaN(hoje)) return null;
    return Math.round((alvo - hoje) / 864e5);
  }

  function idadeTexto(iso) {
    if (!iso) return "sem carimbo de hora";
    const t = new Date(iso).getTime();
    if (isNaN(t)) return "sem carimbo de hora";
    const min = Math.max(0, Math.round((Date.now() - t) / 60000));
    if (min < 2) return "atualizado agora";
    if (min < 90) return "atualizado há " + min + " min";
    if (min < 48 * 60) return "atualizado há " + Math.round(min / 60) + " h";
    return "atualizado há " + Math.round(min / 1440) + " dias";
  }

  function classeIdade(iso) {
    if (!iso) return "mkt-velho";
    const t = new Date(iso).getTime();
    if (isNaN(t)) return "mkt-velho";
    return (Date.now() - t) / 60000 > 90 ? "mkt-velho" : "mkt-fresco";
  }

  function semFonte(txt) {
    return `<span class="mkt-sem">${esc(txt || "sem fonte")}</span>`;
  }

  function avisoSemDados(titulo) {
    return `<div class="mkt-bloco mkt-vazio">` +
      (titulo ? `<div class="mkt-titulo">${esc(titulo)}</div>` : "") +
      `<p class="mkt-aviso">${esc(SEM_DADOS)}</p></div>`;
  }

  /* ------------------------------------------------------------------ estado ---- */

  const API = {
    dados: { mercado: null, precificacao: null },
  };

  async function carrega() {
    const pega = async (caminho) => {
      try {
        if (typeof raiz.fetch !== "function") return null;
        const r = await raiz.fetch(caminho + "?t=" + Date.now());
        if (!r || !r.ok) return null;
        const j = await r.json();
        return j && typeof j === "object" ? j : null;
      } catch (e) { return null; }
    };
    try {
      const res = await Promise.all([
        pega("data/mercado.json"), pega("data/precificacao.json"),
      ]);
      API.dados = { mercado: res[0], precificacao: res[1] };
    } catch (e) {
      API.dados = { mercado: null, precificacao: null };
    }
    if (!API.dados.mercado || !API.dados.precificacao) {
      try {
        console.warn("[mercado] arquivos ausentes:", {
          mercado: !!API.dados.mercado, precificacao: !!API.dados.precificacao,
        });
      } catch (e) { /* ignora */ }
    }
  }

  function pronto() {
    const d = API.dados || {};
    return !!((d.mercado && typeof d.mercado === "object") ||
              (d.precificacao && typeof d.precificacao === "object"));
  }

  function mercado() {
    const d = API.dados || {};
    return d.mercado && typeof d.mercado === "object" ? d.mercado : null;
  }
  function precificacao() {
    const d = API.dados || {};
    return d.precificacao && typeof d.precificacao === "object" ? d.precificacao : null;
  }

  /* ------------------------------------------------------------------ faixa ---- */

  function cartoesHtml(M) {
    const ativos = M && M.ativos && typeof M.ativos === "object" ? M.ativos : {};
    const cartoes = CARTOES.map((c) => {
      const a = ativos[c.chave] && typeof ativos[c.chave] === "object" ? ativos[c.chave] : null;
      const juro = c.tipo === "juro";
      const ultimo = a ? fmt(a.ultimo, c.casas) : null;
      const vDia = a ? (juro ? a.var_dia_bp : a.var_dia_pct) : null;
      const v5d = a ? (juro ? a.var_5d_bp : a.var_5d_pct) : null;
      const suf = juro ? " bp" : "%";
      const casasVar = juro ? 0 : 2;
      const txtDia = fmtVar(vDia, casasVar, suf);
      const txt5d = fmtVar(v5d, casasVar, suf);
      const hora = a ? horaUtc(a.hora_utc) : null;
      const simbolo = a && a.simbolo ? a.simbolo : null;
      const dica = (simbolo ? "Símbolo: " + simbolo + ". " : "") + (hora ? "Cotação de " + hora + "." : "sem fonte");
      return `<div class="mkt-cartao${a ? "" : " mkt-cartao-vazio"}" title="${esc(dica)}">` +
        `<div class="mkt-cartao-rot">${esc(c.rotulo)}` +
          (simbolo ? `<small>${esc(simbolo)}</small>` : "") + `</div>` +
        `<div class="mkt-cartao-num">${ultimo != null
          ? esc((c.prefixo || "") + ultimo + (juro ? "%" : ""))
          : semFonte()}</div>` +
        `<div class="mkt-cartao-vars">` +
          `<span class="${classeVar(vDia, c.tipo)}"><small>dia</small> ${txtDia != null ? esc(txtDia) : semFonte("—")}</span>` +
          `<span class="${classeVar(v5d, c.tipo)}"><small>5 d</small> ${txt5d != null ? esc(txt5d) : semFonte("—")}</span>` +
        `</div>` +
        (juro ? `<div class="mkt-cartao-nota">juro: cor neutra por regra</div>` : "") +
      `</div>`;
    });
    return `<div class="mkt-cartoes">${cartoes.join("")}</div>`;
  }

  function jurosHtml(M) {
    const J = M && M.juros && typeof M.juros === "object" ? M.juros : {};
    const linhas = MOEDAS.map((m) => {
      const j = J[m] && typeof J[m] === "object" ? J[m] : {};
      const y2 = fmt(j.y2, 2);
      const y10 = fmt(j.y10, 2);
      const fonte2 = j.fonte_y2 ? esc(j.fonte_y2) : "sem fonte";
      const fonte10 = j.fonte_y10 ? esc(j.fonte_y10) : null;
      return `<tr>` +
        `<td class="mkt-moeda">${BANDEIRA[m] || ""} <b>${m}</b></td>` +
        `<td class="mkt-num">${y2 != null ? `<b>${esc(y2)}%</b>` : semFonte()}</td>` +
        `<td class="mkt-data">${j.data_y2 ? esc(dataCurta(j.data_y2)) : "—"}</td>` +
        `<td class="mkt-num">${y10 != null ? `${esc(y10)}%` : `<span class="mkt-sem">10a: só EUA</span>`}</td>` +
        `<td class="mkt-data">${j.data_y10 && y10 != null ? esc(dataCurta(j.data_y10)) : "—"}</td>` +
        `<td class="mkt-fonte">${fonte2}${fonte10 ? " · 10a: " + fonte10 : ""}</td>` +
      `</tr>`;
    });
    return `<div class="mkt-sub">` +
      `<div class="mkt-subtitulo">Juro de 2 anos por moeda` +
        `<small>título público de 2 anos; o de 10 anos só quando a fonte cobre</small></div>` +
      `<div class="mkt-rolagem"><table class="mkt-tabela">` +
        `<thead><tr><th>Moeda</th><th class="mkt-num">2 anos</th><th>Data</th>` +
        `<th class="mkt-num">10 anos</th><th>Data</th><th>Fonte</th></tr></thead>` +
        `<tbody>${linhas.join("")}</tbody></table></div></div>`;
  }

  function diferenciaisHtml(M) {
    const D = M && M.diferenciais && typeof M.diferenciais === "object" ? M.diferenciais : null;
    const pares = D ? Object.keys(D) : [];
    if (!pares.length) {
      return `<div class="mkt-sub"><div class="mkt-subtitulo">Diferencial de juros (base − cotada)</div>` +
        `<p class="mkt-aviso">${semFonte("sem fonte para os diferenciais")}</p></div>`;
    }
    const linhas = pares.map((par) => {
      const d = D[par] && typeof D[par] === "object" ? D[par] : {};
      const base = par.slice(0, 3), cotada = par.slice(3, 6);
      const d2 = fmtVar(d.d2y_pp, 2, " pp");
      const d10 = fmtVar(d.d10y_pp, 2, " pp");
      const v5 = fmtVar(d.var_5d_bp, 0, " bp");
      return `<tr>` +
        `<td class="mkt-par"><b>${esc(par)}</b><small>${esc(base)} − ${esc(cotada)}</small></td>` +
        `<td class="mkt-num">${d2 != null ? `<b>${esc(d2)}</b>` : semFonte()}</td>` +
        `<td class="mkt-num">${d10 != null ? esc(d10) : semFonte("10a: só EUA")}</td>` +
        `<td class="mkt-num mkt-neutro">${v5 != null ? esc(v5) : semFonte()}</td>` +
      `</tr>`;
    });
    return `<div class="mkt-sub">` +
      `<div class="mkt-subtitulo">Diferencial de juros (base − cotada)` +
        `<small>2 anos em pontos percentuais; positivo = a moeda-base paga mais. Só exibição: não entra no sentimento.</small></div>` +
      `<div class="mkt-rolagem"><table class="mkt-tabela mkt-tabela-dif">` +
        `<thead><tr><th>Par</th><th class="mkt-num">2 anos</th><th class="mkt-num">10 anos</th>` +
        `<th class="mkt-num">Var. 5 d</th></tr></thead>` +
        `<tbody>${linhas.join("")}</tbody></table></div></div>`;
  }

  function barraProbHtml(b) {
    const pa = eNum(b.p_alta) ? b.p_alta : null;
    const pm = eNum(b.p_manutencao) ? b.p_manutencao : null;
    const pc = eNum(b.p_corte) ? b.p_corte : null;
    if (pa == null && pm == null && pc == null) {
      return `<div class="mkt-barra mkt-barra-vazia" title="sem fonte">${semFonte()}</div>`;
    }
    const seg = (p, cls, rot) => {
      const w = Math.max(0, Math.min(100, Math.round((p || 0) * 100)));
      if (!w) return "";
      return `<i class="${cls}" style="width:${w}%" title="${esc(rot + " " + w + "%")}">` +
        (w >= 14 ? `<span>${w}%</span>` : "") + `</i>`;
    };
    const dica = "alta " + (fmtPct100(pa) || "—") + " · manutenção " + (fmtPct100(pm) || "—") +
      " · corte " + (fmtPct100(pc) || "—");
    return `<div class="mkt-barra" title="${esc(dica)}">` +
      seg(pa, "mkt-seg-alta", "alta") + seg(pm, "mkt-seg-manut", "manutenção") + seg(pc, "mkt-seg-corte", "corte") +
    `</div>`;
  }

  function precificacaoTabelaHtml(P) {
    const B = P && P.bancos && typeof P.bancos === "object" ? P.bancos : {};
    const linhas = MOEDAS.map((m) => {
      const b = B[m] && typeof B[m] === "object" ? B[m] : {};
      const nome = b.banco || NOME_BANCO[m];
      const dias = diasAte(b.proxima);
      const quando = dias == null ? "" : dias === 0 ? "hoje" : dias === 1 ? "amanhã" : dias < 0 ? "passou" : "em " + dias + " d";
      const proxima = b.proxima
        ? `${esc(dataCurta(b.proxima))}<small>${quando}</small>`
        : semFonte("—");
      const taxa = fmt(b.taxa_atual, 3);
      const pr = precificacaoDe(m, null);
      const bp = fmtVar(b.implicito_bp, 1, " bp");
      const qual = b.qualidade || "sem fonte";
      const clsQual = "mkt-qual-" + String(qual).replace(/\s+/g, "-");
      return `<tr>` +
        `<td class="mkt-moeda">${BANDEIRA[m] || ""} <b>${esc(nome)}</b><small>${m}</small></td>` +
        `<td class="mkt-data">${proxima}</td>` +
        `<td class="mkt-num">${taxa != null ? esc(taxa) + "%" : semFonte()}</td>` +
        `<td class="mkt-col-barra">${barraProbHtml(b)}</td>` +
        `<td><span class="mkt-dir ${pr.classe}" title="${esc(pr.titulo)}">${esc(pr.texto)}</span>` +
          (bp != null ? `<small class="mkt-bp">${esc(bp)} implícito</small>` : "") + `</td>` +
        `<td><span class="mkt-qual ${clsQual}">${esc(qual)}</span>` +
          `<small class="mkt-fonte-txt">${b.fonte ? esc(b.fonte) : "sem fonte"}` +
          (b.metodo ? ` · ${esc(b.metodo)}` : "") +
          (b.coletado_em ? ` · ${esc(horaUtc(b.coletado_em))}` : "") + `</small></td>` +
      `</tr>`;
    });
    return `<div class="mkt-sub">` +
      `<div class="mkt-subtitulo">Próxima decisão — o que o mercado precifica` +
        `<small>${P && P.metodo_geral ? esc(P.metodo_geral) : "probabilidades da próxima reunião; barra = alta · manutenção · corte"}</small></div>` +
      `<div class="mkt-legenda"><i class="mkt-seg-alta"></i> alta <i class="mkt-seg-manut"></i> manutenção <i class="mkt-seg-corte"></i> corte</div>` +
      `<div class="mkt-rolagem"><table class="mkt-tabela mkt-tabela-prec">` +
        `<thead><tr><th>Banco</th><th>Próxima</th><th class="mkt-num">Taxa atual</th>` +
        `<th>Probabilidades</th><th>Mercado precifica</th><th>Fonte</th></tr></thead>` +
        `<tbody>${linhas.join("")}</tbody></table></div></div>`;
  }

  function faixaHtml() {
    try {
      const M = mercado();
      const P = precificacao();
      if (!M && !P) return avisoSemDados("Mercado — o que está precificado");
      const carimboM = M ? M.gerado_em : null;
      const carimboP = P ? P.gerado_em : null;
      const cabecalho = `<div class="mkt-cabecalho">` +
        `<div class="mkt-titulo">Mercado — o que está precificado` +
          `<small>dados de mercado e probabilidades; nada disto entra no sentimento</small></div>` +
        `<div class="mkt-frescor">` +
          (M ? `<span class="${classeIdade(carimboM)}">mercado: ${esc(idadeTexto(carimboM))}</span>`
             : `<span class="mkt-velho">mercado: ${esc(SEM_DADOS)}</span>`) +
          (P ? `<span class="${classeIdade(carimboP)}">precificação: ${esc(idadeTexto(carimboP))}</span>`
             : `<span class="mkt-velho">precificação: ${esc(SEM_DADOS)}</span>`) +
          (M && M.fonte ? `<span class="mkt-fonte-txt">fonte: ${esc(M.fonte)}</span>` : "") +
        `</div></div>`;
      const corpoM = M
        ? cartoesHtml(M) + jurosHtml(M) + diferenciaisHtml(M)
        : `<p class="mkt-aviso">${esc("cotações, juros e diferenciais: " + SEM_DADOS)}</p>`;
      const corpoP = P
        ? precificacaoTabelaHtml(P)
        : `<p class="mkt-aviso">${esc("precificação da próxima decisão: " + SEM_DADOS)}</p>`;
      return `<div class="mkt-bloco mkt-faixa">${cabecalho}${corpoM}${corpoP}</div>`;
    } catch (e) {
      try { console.warn("[mercado] faixaHtml falhou:", e && e.message); } catch (_) { /* ignora */ }
      return avisoSemDados("Mercado — o que está precificado");
    }
  }

  /* ------------------------------------------------------------------ comparação ---- */

  // Compara a leitura do HCI com o que o mercado precifica para a moeda. Não altera nada:
  // devolve texto, classes e um tooltip com a conta e a fonte.
  //   leituraHci ∈ {"alta","corte","manutencao",null}
  //   diff ∈ {"alinhado","HCI mais hawkish","HCI mais dovish","divergência","sem fonte"}
  //   (quando há mercado mas não há leitura HCI, diff = "sem leitura" — caso fora do contrato,
  //    declarado aqui para não mentir "sem fonte" quando a fonte existe)
  function precificacaoDe(moeda, leituraHci) {
    const vazio = (motivo) => ({
      texto: "sem fonte", direcao: null, classe: "mkt-sem", diff: "sem fonte", diffClasse: "mkt-sem",
      fonte: null, qualidade: "sem fonte",
      titulo: motivo || "Sem fonte para a precificação desta moeda.",
    });
    try {
      const P = precificacao();
      if (!P || !P.bancos || typeof P.bancos !== "object") return vazio("Precificação: " + SEM_DADOS + ".");
      const b = P.bancos[moeda];
      if (!b || typeof b !== "object") return vazio("Sem registro de precificação para " + moeda + ".");

      const probs = {
        alta: eNum(b.p_alta) ? b.p_alta : null,
        manutencao: eNum(b.p_manutencao) ? b.p_manutencao : null,
        corte: eNum(b.p_corte) ? b.p_corte : null,
      };
      const chaves = Object.keys(probs).filter((k) => probs[k] != null);
      const fonteTxt = b.fonte || null;
      const qualidade = b.qualidade || (chaves.length ? "baixa" : "sem fonte");
      if (!chaves.length) {
        const r = vazio("Sem fonte para a próxima decisão do " + (b.banco || NOME_BANCO[moeda] || moeda) + ".");
        r.fonte = fonteTxt; r.qualidade = qualidade;
        return r;
      }

      // Direção do mercado: a declarada pelo coletor; se faltar, a de maior probabilidade.
      let maior = chaves[0];
      chaves.forEach((k) => { if (probs[k] > probs[maior]) maior = k; });
      const direcao = (b.direcao_mercado && GRAU[b.direcao_mercado] != null) ? b.direcao_mercado : maior;
      const pMax = probs[direcao] != null ? probs[direcao] : probs[maior];
      const texto = Math.round(pMax * 100) + "% " + DIRECAO_TXT[direcao];
      const classe = "mkt-" + (direcao === "manutencao" ? "manut" : direcao);

      const leitura = leituraHci && GRAU[leituraHci] != null ? leituraHci : null;
      let diff, diffClasse, frase;
      if (!leitura) {
        diff = "sem leitura";
        diffClasse = "mkt-sem";
        frase = "Sem leitura HCI para comparar.";
      } else if (leitura === direcao) {
        diff = "alinhado";
        diffClasse = "mkt-diff-ok";
        frase = "Leitura HCI (" + DIRECAO_TXT[leitura] + ") coincide com a direção do mercado.";
      } else if (pMax < 0.5) {
        diff = "divergência";
        diffClasse = "mkt-diff-div";
        frase = "Leitura HCI (" + DIRECAO_TXT[leitura] + ") difere do mercado, e o mercado está dividido (maior probabilidade abaixo de 50%).";
      } else if (GRAU[leitura] > GRAU[direcao]) {
        diff = "HCI mais hawkish";
        diffClasse = "mkt-diff-hawk";
        frase = "Leitura HCI (" + DIRECAO_TXT[leitura] + ") é mais dura que o mercado (" + DIRECAO_TXT[direcao] + ").";
      } else {
        diff = "HCI mais dovish";
        diffClasse = "mkt-diff-dove";
        frase = "Leitura HCI (" + DIRECAO_TXT[leitura] + ") é mais branda que o mercado (" + DIRECAO_TXT[direcao] + ").";
      }

      const bp = fmtVar(b.implicito_bp, 1, " bp");
      const titulo =
        "Mercado precifica: alta " + (fmtPct100(probs.alta) || "sem fonte") +
        " · manutenção " + (fmtPct100(probs.manutencao) || "sem fonte") +
        " · corte " + (fmtPct100(probs.corte) || "sem fonte") +
        (bp != null ? " (variação implícita " + bp + ")" : "") +
        ". Fonte: " + (fonteTxt || "sem fonte") +
        (b.metodo ? " · método " + b.metodo : "") +
        " · qualidade " + qualidade +
        (b.coletado_em ? " · coletado " + horaUtc(b.coletado_em) : "") +
        ". " + frase +
        " Regra: alinhado quando direção = leitura; hawkish/dovish pela escala alta > manutenção > corte; divergência quando a maior probabilidade fica abaixo de 50%.";

      return { texto: texto, direcao: direcao, classe: classe, diff: diff, diffClasse: diffClasse,
               fonte: fonteTxt, qualidade: qualidade, titulo: titulo };
    } catch (e) {
      try { console.warn("[mercado] precificacaoDe falhou:", e && e.message); } catch (_) { /* ignora */ }
      return vazio();
    }
  }

  /* ------------------------------------------------------------------ reação ---- */

  function reacaoHtml() {
    try {
      const M = mercado();
      if (!M) return avisoSemDados("Reação após o último dado");
      const R = M.reacao;
      if (!R || typeof R !== "object") return "";

      const unidade = R.unidade ? " " + R.unidade : "";
      const numRe = (v) => (fmt(v, 1) != null ? esc(fmt(v, 1) + unidade) : semFonte());
      const surpresa = eNum(R.surpresa) ? R.surpresa : null;
      const clsSurp = surpresa == null ? "mkt-neutro" : surpresa > 0 ? "mkt-sobe" : surpresa < 0 ? "mkt-cai" : "mkt-neutro";

      const placar = `<div class="mkt-placar">` +
        `<div><span class="mkt-rot">Atual</span><strong>${numRe(R.atual)}</strong></div>` +
        `<div><span class="mkt-rot">Esperado</span><strong>${numRe(R.esperado)}</strong></div>` +
        `<div><span class="mkt-rot">Anterior</span><strong>${numRe(R.anterior)}</strong></div>` +
        `<div><span class="mkt-rot">Surpresa</span><strong class="${clsSurp}">${surpresa != null ? esc(fmtVar(surpresa, 1, unidade)) : semFonte()}</strong></div>` +
      `</div>`;

      const J = R.janelas && typeof R.janelas === "object" ? R.janelas : {};
      const colunas = [["30min", "30 min"], ["2h", "2 h"], ["ate_agora", "até agora"]];
      const linhasDef = [
        ["DXY_pct", "DXY", "pct"], ["US2Y_bp", "Juro EUA 2 anos", "juro"],
        ["USDJPY_pct", "USD/JPY", "pct"], ["OURO_pct", "Ouro", "pct"], ["ES_pct", "S&P (ES)", "pct"],
      ];
      const linhas = linhasDef.map((def) => {
        const campo = def[0], rot = def[1], tipo = def[2];
        const cels = colunas.map((col) => {
          const jan = J[col[0]] && typeof J[col[0]] === "object" ? J[col[0]] : {};
          const v = jan[campo];
          const txt = tipo === "juro" ? fmtVar(v, 0, " bp") : fmtVar(v, 2, "%");
          return `<td class="mkt-num ${classeVar(v, tipo)}">${txt != null ? esc(txt) : semFonte("—")}</td>`;
        });
        return `<tr><td>${esc(rot)}</td>${cels.join("")}</tr>`;
      });
      const tabela = `<div class="mkt-rolagem"><table class="mkt-tabela mkt-tabela-reacao">` +
        `<thead><tr><th>Ativo</th>${colunas.map((col) => `<th class="mkt-num">${esc(col[1])}</th>`).join("")}</tr></thead>` +
        `<tbody>${linhas.join("")}</tbody></table></div>`;

      const traj = `<p class="mkt-traj"><span class="mkt-rot">Trajetória do USD/JPY</span> ` +
        (R.trajetoria_usdjpy ? esc(R.trajetoria_usdjpy) : semFonte()) + `</p>`;

      const pa = eNum(R.p_fed_antes) ? R.p_fed_antes : null;
      const pd = eNum(R.p_fed_depois) ? R.p_fed_depois : null;
      let fed;
      if (pa != null && pd != null) {
        const delta = Math.round((pd - pa) * 100);
        const clsDelta = delta > 0 ? "mkt-alta" : delta < 0 ? "mkt-corte" : "mkt-neutro";
        fed = `<p class="mkt-fed"><span class="mkt-rot">Probabilidade de alta/corte do Fed</span> ` +
          `<b>${esc(fmtPct100(pa))}</b> → <b>${esc(fmtPct100(pd))}</b> ` +
          `<span class="${clsDelta}">(${delta > 0 ? "+" : ""}${delta} pp)</span>` +
          (R.p_fed_nota ? `<small>${esc(R.p_fed_nota)}</small>` : "") + `</p>`;
      } else {
        fed = `<p class="mkt-fed"><span class="mkt-rot">Probabilidade de alta/corte do Fed</span> ` +
          (R.p_fed_nota ? esc(R.p_fed_nota) : semFonte()) + `</p>`;
      }

      const quando = R.quando_utc ? horaUtc(R.quando_utc) : null;
      const cab = `<div class="mkt-cabecalho">` +
        `<div class="mkt-titulo">Reação após o ${esc(R.evento || "último dado")}` +
          `<small>${R.moeda ? (BANDEIRA[R.moeda] || "") + " " + esc(R.moeda) + " · " : ""}` +
          `${quando ? "divulgado " + esc(quando) : "sem carimbo de hora"}` +
          `${R.fonte ? " · fonte: " + esc(R.fonte) : ""}</small></div></div>`;

      return `<div class="mkt-bloco mkt-reacao">${cab}${placar}${tabela}${traj}${fed}</div>`;
    } catch (e) {
      try { console.warn("[mercado] reacaoHtml falhou:", e && e.message); } catch (_) { /* ignora */ }
      return "";
    }
  }

  /* ------------------------------------------------------------------ estilo ---- */

  const CSS = `
   /* módulo de mercado — tokens vindos do theme.css (--font-mono, --accent, --positive,
      --negative, --warn) e da profundidade definida em ui_macro.js */
   .mkt-bloco{margin-bottom:28px;border:1px solid rgba(255,255,255,.06);border-radius:14px;padding:18px 20px;
     background:linear-gradient(180deg,rgba(255,255,255,.035),rgba(255,255,255,.012));
     box-shadow:0 1px 0 rgba(255,255,255,.03) inset,0 10px 30px -18px rgba(0,0,0,.7)}
   .mkt-bloco.mkt-vazio{border-style:dashed;opacity:.8}
   .mkt-cabecalho{display:flex;justify-content:space-between;align-items:flex-start;gap:14px;flex-wrap:wrap;margin-bottom:14px}
   .mkt-titulo{font-size:16px;font-weight:600;letter-spacing:-.01em}
   .mkt-titulo small{display:block;font-size:12px;font-weight:400;opacity:.6;margin-top:3px;line-height:1.45}
   .mkt-frescor{display:flex;gap:10px;flex-wrap:wrap;font-size:12px;align-items:center}
   .mkt-fresco{color:var(--positive,#52d98a)}
   .mkt-velho{color:var(--warn,#f0b429)}
   .mkt-aviso{font-size:13px;opacity:.75;margin:6px 0;line-height:1.5}
   .mkt-sem{opacity:.5;font-style:italic;font-size:12px}
   .mkt-rot{display:block;font-size:10.5px;letter-spacing:.12em;text-transform:uppercase;opacity:.55;margin-bottom:4px}
   .mkt-fonte-txt{display:block;font-size:12px;opacity:.6;line-height:1.4}
   /* cartões */
   .mkt-cartoes{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:10px;margin-bottom:18px}
   .mkt-cartao{border:1px solid rgba(255,255,255,.07);border-radius:11px;padding:12px 14px;min-width:0;
     background:linear-gradient(180deg,rgba(255,255,255,.03),rgba(255,255,255,.008))}
   .mkt-cartao-vazio{border-style:dashed;opacity:.7}
   .mkt-cartao-rot{font-size:12px;letter-spacing:.04em;opacity:.7;display:flex;justify-content:space-between;gap:6px}
   .mkt-cartao-rot small{font-family:var(--font-mono);font-size:10px;opacity:.55}
   .mkt-cartao-num{font-size:24px;font-weight:700;letter-spacing:-.02em;line-height:1.15;margin:6px 0 6px;
     font-family:var(--font-mono);font-variant-numeric:tabular-nums}
   .mkt-cartao-vars{display:flex;gap:10px;flex-wrap:wrap;font-size:12.5px;font-family:var(--font-mono)}
   .mkt-cartao-vars small{opacity:.5;font-family:inherit;margin-right:3px;font-size:11px}
   .mkt-cartao-nota{font-size:11px;opacity:.4;margin-top:5px}
   .mkt-sobe{color:var(--positive,#52d98a)}
   .mkt-cai{color:var(--negative,#f87a7a)}
   .mkt-neutro{color:inherit;opacity:.85}
   /* tabelas */
   .mkt-sub{margin-top:18px}
   .mkt-subtitulo{font-size:14px;font-weight:600;margin-bottom:8px}
   .mkt-subtitulo small{display:block;font-size:12px;font-weight:400;opacity:.6;margin-top:2px;line-height:1.45}
   .mkt-rolagem{overflow-x:auto;-webkit-overflow-scrolling:touch}
   .mkt-tabela{width:100%;border-collapse:collapse;font-size:13.5px}
   .mkt-tabela th{font-size:11px;letter-spacing:.08em;text-transform:uppercase;opacity:.55;text-align:left;
     padding:6px 10px;border-bottom:1px solid rgba(255,255,255,.08);white-space:nowrap}
   .mkt-tabela td{padding:8px 10px;border-bottom:1px solid rgba(255,255,255,.05);vertical-align:middle}
   .mkt-tabela tr:hover td{background:rgba(255,255,255,.03)}
   .mkt-tabela td small{display:block;font-size:12px;opacity:.6;margin-top:2px}
   .mkt-num{text-align:right;white-space:nowrap;font-family:var(--font-mono);font-variant-numeric:tabular-nums}
   .mkt-tabela th.mkt-num{text-align:right}
   .mkt-tabela td.mkt-num b{font-size:15px;font-weight:600}
   .mkt-moeda b{font-size:14px}
   .mkt-data{font-family:var(--font-mono);font-size:12.5px;white-space:nowrap}
   .mkt-fonte{font-size:12px;opacity:.65;max-width:26ch}
   .mkt-par small{font-family:var(--font-mono)}
   /* precificação */
   .mkt-legenda{display:flex;gap:6px;align-items:center;font-size:12px;opacity:.75;margin:0 0 8px}
   .mkt-legenda i{display:inline-block;width:12px;height:8px;border-radius:2px;margin-left:8px}
   .mkt-col-barra{min-width:180px}
   .mkt-barra{display:flex;height:18px;border-radius:5px;overflow:hidden;background:rgba(255,255,255,.06);min-width:160px}
   .mkt-barra i{display:block;height:100%;font-style:normal;font-size:11px;line-height:18px;text-align:center;
     color:#07130f;font-weight:600;font-family:var(--font-mono);white-space:nowrap;overflow:hidden}
   .mkt-barra-vazia{align-items:center;justify-content:center;background:transparent;border:1px dashed rgba(255,255,255,.18)}
   .mkt-seg-alta{background:var(--positive,#52d98a)}
   .mkt-seg-manut{background:rgba(170,182,200,.55)}
   .mkt-seg-corte{background:var(--negative,#f87a7a)}
   .mkt-dir{display:inline-block;font-size:13px;font-weight:600;padding:2px 9px;border-radius:20px;white-space:nowrap}
   .mkt-alta{color:var(--positive,#52d98a);background:rgba(82,217,138,.12)}
   .mkt-corte{color:var(--negative,#f87a7a);background:rgba(248,122,122,.14)}
   .mkt-manut{color:inherit;background:rgba(255,255,255,.07)}
   span.mkt-dir.mkt-sem{font-style:italic;font-weight:400;background:transparent;border:1px dashed rgba(255,255,255,.18)}
   .mkt-bp{font-family:var(--font-mono);font-size:12px}
   .mkt-qual{font-size:10.5px;letter-spacing:.07em;text-transform:uppercase;padding:2px 7px;border-radius:20px;
     border:1px solid rgba(255,255,255,.14);white-space:nowrap}
   .mkt-qual-alta{border-color:rgba(94,234,212,.5);color:var(--accent,#5eead4)}
   .mkt-qual-media{border-color:rgba(240,180,41,.5);color:var(--warn,#f0b429)}
   .mkt-qual-baixa{border-color:rgba(248,122,122,.45);color:var(--negative,#f87a7a)}
   .mkt-qual-sem-fonte{opacity:.45;border-style:dashed}
   /* diferença Leitura HCI × Mercado (classes usadas pela tabela de bancos em ui_macro.js) */
   .mkt-diff-ok{color:var(--accent,#5eead4)}
   .mkt-diff-hawk{color:var(--positive,#52d98a)}
   .mkt-diff-dove{color:var(--negative,#f87a7a)}
   .mkt-diff-div{color:var(--warn,#f0b429)}
   /* reação */
   .mkt-placar{display:grid;grid-template-columns:repeat(auto-fit,minmax(120px,1fr));gap:12px;margin:0 0 14px}
   .mkt-placar strong{display:block;font-size:22px;font-weight:700;letter-spacing:-.01em;font-family:var(--font-mono);
     font-variant-numeric:tabular-nums}
   .mkt-traj,.mkt-fed{font-size:13.5px;line-height:1.55;margin:12px 0 0}
   .mkt-traj .mkt-rot,.mkt-fed .mkt-rot{display:inline;margin:0 6px 0 0}
   .mkt-fed b{font-family:var(--font-mono);font-size:15px}
   .mkt-fed small{display:block;font-size:12px;opacity:.6;margin-top:3px}
   @media (max-width:640px){
     .mkt-bloco{padding:14px}
     .mkt-cartao-num{font-size:20px}
     .mkt-col-barra{min-width:140px}
     .mkt-barra{min-width:130px}
   }
  `;

  function injetaEstilo() {
    try {
      const doc = raiz.document;
      if (!doc || typeof doc.createElement !== "function") return;
      if (typeof doc.querySelector === "function" && doc.querySelector("style[data-hci-mercado]")) return;
      const estilo = doc.createElement("style");
      if (typeof estilo.setAttribute === "function") estilo.setAttribute("data-hci-mercado", "1");
      estilo.textContent = CSS;
      const alvo = doc.head || (doc.getElementsByTagName ? doc.getElementsByTagName("head")[0] : null) || doc.body;
      if (alvo && typeof alvo.appendChild === "function") alvo.appendChild(estilo);
    } catch (e) { /* sem DOM: nada a injetar */ }
  }
  injetaEstilo();

  /* ------------------------------------------------------------------ exporta ---- */

  API.carrega = carrega;
  API.pronto = pronto;
  API.faixaHtml = faixaHtml;
  API.precificacaoDe = precificacaoDe;
  API.reacaoHtml = reacaoHtml;
  raiz.HCI_MERCADO = API;
})();
