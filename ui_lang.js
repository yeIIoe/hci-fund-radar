/* IDIOMA — portugues nativo no painel, sem tradutor de maquina.
 *
 * O PROBLEMA (Eduardo, 04/set): o Chrome traduzindo o painel "em todos" virava "actual" em
 * "na verdade", "landed" em "pousou", e o layout refluia. Traducao de maquina nao conhece o
 * vocabulario do dominio.
 *
 * O MECANISMO: o mesmo que limpaFundDaTela ja usa — troca de texto no DOM, nunca nos
 * templates. Os textos da tela continuam em ingles na fonte (ui_macro.js e os JSONs do
 * Python); este modulo passa pelos nos de texto e substitui os que conhece. O que ele nao
 * conhece fica em ingles, legivel — nunca fica quebrado. Um MutationObserver reaplica a cada
 * redesenho (troca de aba, clique em par, dia do calendario).
 *
 * PADRAO: o idioma do navegador (pt -> portugues), com seletor PT | EN no cabecalho e a
 * escolha guardada no navegador. Em portugues, <html lang="pt-BR"> — o Chrome para de
 * oferecer traducao, porque a pagina ja esta no idioma dele.
 */
(function () {
  "use strict";

  function idiomaAtual() {
    try {
      const g = localStorage.getItem("mac_lang");
      if (g === "pt" || g === "en") return g;
    } catch (e) { /* sem storage */ }
    const nav = (navigator.language || "").toLowerCase();
    return nav.startsWith("pt") ? "pt" : "en";
  }

  /* ----------------------------------------------------------- DICIONARIO EXATO
   * chave = o texto do no, sem espacos nas pontas, exatamente como sai do render */
  const EXATO = {
    // cabecalho e navegacao (index.html / app.js)
    "Time cut": "Corte de tempo", "Refresh": "Atualizar", "Exit": "Sair",
    "Previous": "Anterior", "Next": "Próximo", "Loading": "Carregando",
    "Overview": "Visão geral", "Yields": "Juros", "Calendar": "Calendário", "Pairs": "Pares",
    "Equities": "Ações", "News": "Notícias", "Sources": "Fontes",
    "Radar": "Radar", "Macro": "Macro", "Analysis": "Análise", "Method": "Método", "Other": "Outros",
    "Reading panel. It gives the fundamental side; the entry is yours.":
      "Painel de leitura. Ele dá o lado fundamental; a entrada é sua.",
    "Showing only what was known on": "Mostrando só o que se sabia em",
    ". Outcomes and later days are hidden.": ". Resultados e dias posteriores ficam ocultos.",

    // visao geral — reunioes
    "Central bank meetings": "Reuniões dos bancos centrais",
    "Currency": "Moeda", "Policy rate": "Taxa básica", "Last change": "Última mudança",
    "Next decision": "Próxima decisão", "Reading for next move": "Leitura do próximo passo",
    "Local time": "Hora local",
    "today": "hoje", "tomorrow": "amanhã", "no date published": "sem data publicada",
    "no fixed release time": "sem hora fixa", "decides today": "decide hoje", "no date": "sem data",
    "reading not built yet": "leitura ainda não construída",
    "forward reading not built yet": "leitura para frente ainda não construída",
    "Freshness unknown — the calendar file has no timestamp.":
      "Frescor desconhecido — o arquivo do calendário não tem carimbo.",
    "Source delivery, measured this run:": "Entrega da fonte, medida nesta rodada:",
    "— this one is late.": "— esta está atrasada.",
    "The 15-minute clock above is slower than the source.":
      "O relógio de 15 minutos acima é mais lento que a fonte.",

    // visao geral — Estados Unidos
    "United States": "Estados Unidos",
    "Next FOMC decision": "Próxima decisão do FOMC", "day": "dia", "days": "dias",
    "with projections · dot plot": "com projeções · dot plot", "Fed funds": "Fed funds",
    "indicator": "indicador", "latest": "último", "m/m": "m/m", "y/y": "a/a", "month": "mês",
    "CPI headline": "CPI cheio", "CPI core": "CPI núcleo", "Nonfarm payrolls": "Payrolls (NFP)",
    "Unemployment rate": "Taxa de desemprego", "Average hourly earnings": "Salário médio por hora",
    "Participation rate": "Taxa de participação", "prelim": "prelim",
    "What Fed speakers said": "O que os dirigentes do Fed disseram",
    "policy sentences pulled by expression match — a pointer to what to read, not a reading":
      "frases de postura extraídas por expressão — um ponteiro do que ler, não uma leitura",
    "no policy markers": "sem marcadores de política", "by count": "por contagem",
    "Latest from the Fed": "Últimos comunicados do Fed",
    "The newest prints describe": "Os dados mais novos descrevem",
    "Delivery (release → here):": "Entrega (release → aqui):",
    "not measured yet": "ainda não medida",
    "One leg of most pairs, and the rate that gold, NQ and ES answer to. Read straight from the BLS and the Fed — no intermediary.":
      "Uma das pernas da maioria dos pares, e o juro ao qual ouro, NQ e ES respondem. Lido direto do BLS e do Fed — sem intermediário.",
    "Current policy rate, when each one decides next, and the forward reading — what the released data, the speeches and the cycle say it will do. Times are local with the IANA zone — three daylight-saving switches fall inside this calendar.":
      "Taxa básica atual, quando cada um decide de novo, e a leitura para frente — o que os dados divulgados, os discursos e o ciclo dizem que ele fará. Horários locais com o fuso IANA — três trocas de horário de verão caem dentro deste calendário.",
    "Each pair read leg by leg: what each central bank is leaning to do next, and whether the two legs diverge. A reading of the fundamental side — the entry is yours.":
      "Cada par lido perna por perna: para onde cada banco central está inclinado, e se as duas pernas divergem. Uma leitura do lado fundamental — a entrada é sua.",
    "The rate and the dates are facts, checked against each central bank's own pages on 1 Sep 2026. What each one will":
      "A taxa e as datas são fatos, conferidos nas páginas de cada banco central em 01/set/2026. O que cada um vai",
    "do": "fazer",
    "is a separate reading — it comes from the released data, never from a score.":
      "é uma leitura à parte — vem dos dados divulgados, nunca de uma pontuação.",
    "Still missing: speeches are wired for the Fed only, and the market dimension has no free source. So today the ceiling is 75% for USD and 50% for the other seven.":
      "Ainda falta: discursos ligados só para o Fed, e a dimensão de mercado não tem fonte gratuita. Hoje o teto é 75% para o USD e 50% para as outras sete.",
    "This is a reading of the fundamental side, not a signal: the earlier FUND was closed as an entry rule after 15 null tests. The entry is yours.":
      "Isto é uma leitura do lado fundamental, não um sinal: o FUND anterior foi encerrado como regra de entrada depois de 15 testes nulos. A entrada é sua.",
    "Which leg carries the weight matters. On 2 Sep the GBPNZD move was": "Qual perna carrega o peso importa. Em 02/set o movimento do GBPNZD foi",
    "82% the kiwi": "82% o kiwi", "90% the yen": "90% o iene",
    "; the same day EURJPY was": "; no mesmo dia o EURJPY foi",
    ". When the reason sits on one leg, every pair sharing that leg is the same bet.":
      ". Quando a razão está numa perna, todo par que compartilha essa perna é a mesma aposta.",
    "Four dimensions, 25% each:": "Quatro dimensões, 25% cada:",
    "Four dimensions, 25% each, none of them a yield:": "Quatro dimensões, 25% cada, nenhuma delas um yield:",
    "(news intensity from GDELT: an energy spike is an inflation push, a conflict spike a growth risk; quiet weeks do not vote). Conviction is the share of voting dimensions that agree — a missing or quiet dimension lowers the ceiling, it never counts as zero.":
      "(intensidade do noticiário no GDELT: pico de energia é empurrão de inflação, pico de conflito é risco de crescimento; semanas quietas não votam). A convicção é a fração das dimensões que votam e concordam — dimensão ausente ou quieta baixa o teto, nunca conta como zero.",
    "Still missing: speeches are wired for the Fed, ECB, BoE, BoJ and BoC only (RBA and RBNZ block automation, the SNB has no feed), and the geopolitics rule counts by the owner's decision but has not been measured yet.":
      "Ainda falta: discursos ligados só para Fed, BCE, BoE, BoJ e BoC (RBA e RBNZ bloqueiam automação, o SNB não tem feed), e a regra de geopolítica conta por decisão do dono mas ainda não foi medida.",
    "(surprises since the bank last decided, weighted by family and impact, half-life 21 days),":
      "(surpresas desde a última decisão do banco, pesadas por família e impacto, meia-vida de 21 dias),",
    "(hawkish/dovish markers in what the bank's people said),": "(marcadores hawkish/dovish no que os dirigentes disseram),",
    "(the last move, if under six months old) and": "(o último movimento, se tiver menos de seis meses) e",
    "(implied probability). Conviction is the share of connected dimensions that agree — a missing dimension lowers the ceiling, it never counts as zero.":
      "(probabilidade implícita). A convicção é a fração das dimensões ligadas que concordam — dimensão ausente baixa o teto, nunca conta como zero.",

    // pares
    "Leaning to hike": "Inclinado a subir", "On hold": "Em manutenção", "Leaning to cut": "Inclinado a cortar",
    "Last move up": "Último movimento para cima", "Last move down": "Último movimento para baixo",
    "All": "Todos", "With a thesis": "Com tese", "No trade": "Sem tese", "Deciding soon": "Decide em breve",
    "no trade": "sem tese", "no edge": "sem vantagem", "same side": "mesmo lado", "divergence": "divergência",
    "With the Fed's dimensions cancelling out, there is no fundamental push on this instrument.":
      "Com as dimensões do Fed se cancelando, não há empurrão fundamental neste instrumento.",
    "The pair: each currency gets a score from −1 to +1 (each voting dimension adds +0.25 for hike, −0.25 for cut, 0 for hold). The pair reads the difference between its two legs — the sign gives the direction, the size gives the confidence (a 0.50 edge is 25% of the maximum 2.00). Every pair gets a reading; \"no edge\" only when the two legs tie exactly.":
      "O par: cada moeda ganha um score de −1 a +1 (cada dimensão que vota soma +0,25 para alta, −0,25 para corte, 0 para manutenção). O par lê a diferença entre as duas pernas — o sinal dá a direção, o tamanho dá a confiança (uma vantagem de 0,50 é 25% do máximo 2,00). Todo par recebe uma leitura; \"sem vantagem\" só quando as duas pernas empatam exatamente.",
    "SAME SIDE": "MESMO LADO", "CYCLE DIVERGENCE": "DIVERGÊNCIA DE CICLO",
    "data current": "dados atuais", "freshness unknown": "frescor desconhecido",
    "No pair matches this filter.": "Nenhum par cai neste filtro.",
    "Pick a pair on the left.": "Escolha um par à esquerda.",
    "Each pair is two currencies. This panel reads both legs, because the reason for an entry usually sits on one side, not on the pair.":
      "Par é duas moedas. Este painel lê as duas pernas, porque a razão de uma entrada costuma estar de um lado, não no par.",
    "base": "base", "quote": "cotada", "the leg that drives it": "a perna que manda",
    "Reading for the next move": "Leitura do próximo passo",
    "data": "dados", "speeches": "discursos", "cycle": "ciclo", "market": "mercado", "quiet": "quieta",
    "hike": "alta", "hold": "manutenção", "cut": "corte",
    "because": "porque", "last move up": "último movimento: alta", "last move down": "último movimento: corte",
    "next decision": "próxima decisão", "latest prints": "últimos dados",
    "no print with a forecast in the window": "nenhum dado com previsão na janela",
    "no data": "sem dados",
    "Same position on both legs — no fundamental thesis on this axis.":
      "Mesma posição nas duas pernas — sem tese fundamental neste eixo.",
    "The reason sits on": "A razão está em", "Both legs carry the reason.": "As duas pernas carregam a razão.",
    "Same bet as": "Mesma aposta que",
    "— holding two does not diversify, it doubles.": "— segurar dois não diversifica, dobra.",
    "The two central banks last moved in opposite directions. That is the necessary condition for a fundamental thesis — not a sufficient one.":
      "Os dois bancos centrais moveram em direções opostas da última vez. É a condição necessária para uma tese fundamental — não a suficiente.",
    "Both central banks last moved the same way. No divergence to trade on this axis.":
      "Os dois bancos centrais moveram para o mesmo lado. Sem divergência para operar neste eixo.",
    "How this reading is built, and what is still missing": "Como esta leitura é montada, e o que ainda falta",
    "channel": "canal", "measured in-house": "medido em casa",
    "measured correlation with US rates — 5 years, non-overlapping blocks":
      "correlação medida com o juro americano — 5 anos, blocos sem sobreposição",
    "rate": "juro", "same day": "mesmo dia", "same 20 d": "mesmos 20 d", "same 60 d": "mesmos 60 d",
    "next day": "dia seguinte", "next 5 d": "5 d seguintes",
    "US 2-year nominal": "EUA 2 anos nominal", "US 10-year nominal": "EUA 10 anos nominal",
    "US 10-year real (TIPS)": "EUA 10 anos real (TIPS)",
    "With the Fed read as on hold, there is no fundamental push on this instrument.":
      "Com o Fed lido em manutenção, não há empurrão fundamental neste instrumento.",
    "The USD reading is not built yet.": "A leitura do USD ainda não foi construída.",
    "Gold": "Ouro", "Nasdaq 100": "Nasdaq 100", "S&P 500": "S&P 500",
    "real rates: a hawkish USD reading lifts real yields and gold falls; a dovish one does the opposite. Geopolitics enters directly: a conflict spike is safe-haven demand for gold":
      "juro real: uma leitura hawkish do USD sobe o juro real e o ouro cai; uma dovish faz o oposto. A geopolítica entra direto: pico de conflito é demanda de refúgio pelo ouro",
    "discount rate: a higher expected policy rate compresses equity multiples, and long-duration tech most of all. A conflict spike is risk-off for equities":
      "taxa de desconto: juro básico esperado mais alto comprime múltiplos de ações, e a tecnologia de duração longa mais que tudo. Pico de conflito é risk-off para ações",
    "discount rate: same channel as NQ, with less duration and more earnings sensitivity to growth. A conflict spike is risk-off for equities":
      "taxa de desconto: mesmo canal do NQ, com menos duração e mais sensibilidade dos lucros ao crescimento. Pico de conflito é risk-off para ações",
    "NOT measured in-house yet — correlacao_juros.py has not run":
      "AINDA NÃO medido em casa — correlacao_juros.py não rodou",
    "a reading of the fundamental side over weeks, not an entry rule: on 88 manual trades the dollar at the minute correlated +0.26 with gold and broke 41% of the time (DXY filter reproved).":
      "uma leitura do lado fundamental em semanas, não uma regra de entrada: em 88 operações manuais o dólar no minuto correlacionou +0,26 com o ouro e quebrou 41% das vezes (filtro do DXY reprovado).",
    "contemporaneous columns describe the same window; the predictive columns are what an entry would need — and they sit inside noise. Rates describe the month, not the candle.":
      "as colunas contemporâneas descrevem a mesma janela; as preditivas são o que uma entrada precisaria — e ficam dentro do ruído. O juro descreve o mês, não a vela.",

    // geopolitica
    "Geopolitics": "Geopolítica", "World backdrop": "Pano de fundo mundial",
    "geopolitics": "geopolítica", "no spike this week": "sem pico nesta semana",
    "News intensity by currency: articles in the last 3 days against the 14-day daily mean, from GDELT. The implication next to each card is a declared rule — it does not count toward the conviction until it is measured.":
      "Intensidade do noticiário por moeda: artigos dos últimos 3 dias contra a média diária de 14 dias, do GDELT. A implicação ao lado de cada cartão é uma regra declarada — não conta na convicção até ser medida.",
    "Rule, not measurement: a conflict spike tends to send flow to USD, CHF and JPY and out of AUD, NZD and CAD; an energy spike is an inflation push for importers. The hypothesis to test before it ever scores: does a conflict z ≥ 2 change the 20-day return of the risk currencies?":
      "Regra, não medição: um pico de conflito tende a mandar fluxo para USD, CHF e JPY e tirar de AUD, NZD e CAD; um pico de energia é empurrão de inflação para importadores. A hipótese a testar antes de pontuar: um z de conflito ≥ 2 muda o retorno de 20 dias das moedas de risco?",

    // calendario
    "Macro calendar": "Calendário macro", "All currencies": "Todas as moedas",
    "Mon": "Seg", "Tue": "Ter", "Wed": "Qua", "Thu": "Qui", "Fri": "Sex", "Sat": "Sáb", "Sun": "Dom",
    "Reading of the day": "Leitura do dia",
    "Pick a day on the calendar above.": "Escolha um dia no calendário acima.",
    "Nothing above low impact scheduled this day.": "Nada acima de impacto baixo agendado neste dia.",
    "Each release, what it is measured against, and what each outcome would push on the rate decision.":
      "Cada divulgação, contra o que ela é medida, e o que cada desfecho empurraria na decisão de juros.",
    "Scheduled releases and central bank decisions. Pick a day to read what each one would push on the rate decision.":
      "Divulgações agendadas e decisões de bancos centrais. Escolha um dia para ler o que cada uma empurraria na decisão de juros.",
    "No scheduled release this day.": "Nenhuma divulgação agendada neste dia.",
    "Only low-impact releases this day.": "Só divulgações de impacto baixo neste dia.",
    "High": "Alto", "Medium": "Médio", "Low": "Baixo",
    "forecast": "previsão", "previous": "anterior", "actual": "real", "not out": "não saiu",
    "not in the source yet": "ainda não na fonte", "not carried by the fallback source": "a fonte reserva não traz o resultado",
    "= forecast": "= previsão", "time tentative": "hora a confirmar", "preliminary print": "dado preliminar",
    "well above": "muito acima", "in line": "em linha", "well below": "muito abaixo",
    "above forecast": "acima da previsão", "below forecast": "abaixo da previsão",
    "TIGHTENING": "APERTO", "EASING": "ALÍVIO", "nothing — already in the price": "nada — já está no preço",
    "pushes toward TIGHTENING": "empurra para APERTO", "pushes toward EASING": "empurra para ALÍVIO",
    "came in as expected — does not change what was already priced":
      "veio como esperado — não muda o que já estava no preço",
    "no bar to measure against": "sem barra para medir",
    "not in the reading — indicator not mapped to a family": "fora da leitura — indicador sem família",
    "a speech — no number to measure; the text is the release":
      "um discurso — sem número para medir; o texto é a divulgação",
    "no forecast published — a surprise cannot be measured":
      "sem previsão publicada — a surpresa não pode ser medida",
    "released without a published forecast — the surprise cannot be measured":
      "divulgado sem previsão publicada — a surpresa não pode ser medida",
    "indicator not mapped to a family — it does not enter the reading, and that is declared":
      "indicador sem família — não entra na leitura, e isso fica declarado",
    "decides": "decide",

    // as familias (leitor_regras.py) — o "porque" de cada indicador
    "What the central bank actually targets. Core above forecast is the strongest case for tightening there is: it removes the 'it was energy and food' alibi.":
      "O que o banco central de fato mira. Núcleo acima da previsão é o argumento mais forte que existe para apertar: tira o álibi do 'foi energia e alimento'.",
    "It matters, but the central bank discounts energy and food shocks. A high headline with a well-behaved core weighs LESS than the number suggests.":
      "Importa, mas o banco central desconta choques de energia e alimento. Cheio alto com núcleo comportado pesa MENOS do que o número sugere.",
    "Central banks fear de-anchoring more than the current level. Rising expectations trigger tightening even while current inflation falls.":
      "Bancos centrais temem a desancoragem mais do que o nível atual. Expectativas subindo disparam aperto mesmo com a inflação corrente caindo.",
    "A tight labour market sustains wages and services, the stubborn part of inflation. Strong reading = hawkish.":
      "Mercado de trabalho apertado sustenta salários e serviços, a parte teimosa da inflação. Dado forte = hawkish.",
    "INVERTED sign: unemployment above forecast means slack, and slack removes the urgency to tighten.":
      "Sinal INVERTIDO: desemprego acima da previsão é folga, e folga tira a urgência de apertar.",
    "The link between labour and services inflation. For the BoJ and the BoE it is the number they publicly say they are waiting for.":
      "O elo entre trabalho e inflação de serviços. Para o BoJ e o BoE é o número que eles dizem publicamente estar esperando.",
    "High frequency and noisy. Useful for a turn in trend, not for a level.":
      "Alta frequência e ruidoso. Serve para virada de tendência, não para nível.",
    "A survey, not hard data, and it lands before everything else. Above 50 means expansion. Useful for DIRECTION and EARLINESS, not magnitude. The PRICES PAID sub-index counts as inflation, not as activity.":
      "Pesquisa, não dado duro, e sai antes de tudo. Acima de 50 é expansão. Serve para DIREÇÃO e ANTECEDÊNCIA, não para magnitude. O subíndice de PREÇOS PAGOS conta como inflação, não como atividade.",
    "Confirms the state, but it is LATE — it covers a quarter that already ended. It moves the decision little, because the bank already saw the monthly parts.":
      "Confirma o estado, mas é ATRASADO — cobre um trimestre que já acabou. Move pouco a decisão, porque o banco já viu as partes mensais.",
    "Domestic demand, which is what the policy rate actually controls.":
      "Demanda doméstica, que é o que a taxa básica de fato controla.",
    "Lower weight in a service economy; still matters in Germany and Japan.":
      "Peso menor numa economia de serviços; ainda importa na Alemanha e no Japão.",
    "A mood survey. It leads, but it misses often. Low weight on purpose.":
      "Pesquisa de humor. Antecipa, mas erra com frequência. Peso baixo de propósito.",
    "The channel most sensitive to rates — it reacts first when tightening bites.":
      "O canal mais sensível ao juro — reage primeiro quando o aperto morde.",
    "Low weight except in AUD, NZD and CAD, where terms of trade genuinely matter.":
      "Peso baixo, exceto em AUD, NZD e CAD, onde os termos de troca importam de verdade.",
    "Where the GUIDANCE usually appears. Weight is 0 because how much it matters varies by central bank — measure before scoring.":
      "Onde a ORIENTAÇÃO costuma aparecer. Peso 0 porque quanto importa varia por banco central — medir antes de pontuar.",
    "It does not feed the running score — it CLOSES the cycle. What matters here is the outcome against expectations and, above all, the GUIDANCE. On 8 Jul 2026 the RBNZ hike was already priced and price moved only on the guidance — which came in the STATEMENT at 14:00 NZ, not in the press conference at 15:00, which moved nothing (3.9 pips of range).":
      "Não alimenta o acumulado — FECHA o ciclo. O que importa aqui é o desfecho contra a expectativa e, acima de tudo, a ORIENTAÇÃO. Em 08/jul/2026 a alta do RBNZ já estava no preço e o preço só andou na orientação — que veio no COMUNICADO às 14:00 NZ, não na coletiva das 15:00, que não moveu nada (3,9 pips de amplitude).",
  };

  /* ---------------------------------------------------------- PADROES COM NUMERO */
  const MESES = { January: "janeiro", February: "fevereiro", March: "março", April: "abril", May: "maio",
    June: "junho", July: "julho", August: "agosto", September: "setembro", October: "outubro",
    November: "novembro", December: "dezembro" };
  const REGEX = [
    [/^in (\d+) days$/, "em $1 dias"],
    [/^(\d+)d$/, "$1d"],
    [/^Calendar data just now$/, "Dados do calendário de agora"],
    [/^Calendar data (\d+) minutes ago$/, "Dados do calendário de $1 minutos atrás"],
    [/^Calendar data (\d+) hours ago$/, "Dados do calendário de $1 horas atrás"],
    [/^· refreshed every ~15 min, though scheduled runs can lag at peak hours\.?$/,
      "· atualizado a cada ~15 min, embora as rodadas agendadas atrasem em horário de pico."],
    [/^Fallback source active: (.*)$/, "Fonte reserva ativa: $1"],
    [/^high-impact prints land\s*$/, "dados de alto impacto chegam"],
    [/^after the scheduled time \(median, n=(\d+); p90 (.+?) — a late stamp usually means a revision re-touched the record\)\.?\s*(.*)$/,
      (m, n, p90, cauda) => "depois da hora agendada (mediana, n=" + n + "; p90 " + p90 +
        " — carimbo tardio costuma ser revisão retocando o registro)." +
        (/slower than the source/.test(cauda) ? " O relógio de 15 minutos acima é mais lento que a fonte." : (cauda ? " " + cauda : ""))],
    [/^(data|speeches|cycle|market|geopolitics) (✓|✗|—)$/, (m, d, s) => ({ data: "dados", speeches: "discursos", cycle: "ciclo", market: "mercado", geopolitics: "geopolítica" })[d] + " " + s],
    [/^ceiling (\d+)% — (\d) of (\d) dimensions voting$/, "teto $1% — $2 de $3 dimensões votando"],
    [/^(\d+) of (\d+) dimensions voting$/, "$1 de $2 dimensões votando"],
    [/^(▲|▼|—) last move (up|down)$/, (m, s, d) => s + " último movimento: " + (d === "up" ? "alta" : "corte")],
    [/^(▲|▼|—) unchanged$/, "$1 sem mudança"],
    [/^— (\d+) months? back\. That is the month that ended, not a delivery delay; every terminal has the same lag\.\s*(Delivery \(release → here\):)?\s*$/,
      (m, n, cauda) => "— " + n + (n === "1" ? " mês" : " meses") + " atrás. É o mês que acabou, não atraso de entrega; todo terminal tem a mesma defasagem." + (cauda ? " Entrega (release → aqui):" : "")],
    [/^\. That is the month that ended, not a delivery delay; every terminal has the same lag\.\s*(Delivery \(release → here\):)?\s*$/,
      (m, cauda) => ". É o mês que acabou, não atraso de entrega; todo terminal tem a mesma defasagem." + (cauda ? " Entrega (release → aqui):" : "")],
    [/^(.+?)\. Same position on both legs — no fundamental thesis on this axis\.$/,
      "$1. Mesma posição nas duas pernas — sem tese fundamental neste eixo."],
    [/^(\d+) of (\d+) dimensions connected$/, "$1 de $2 dimensões ligadas"],
    [/^landed \+(.+)$/, "chegou +$1"],
    [/^([+\-−]?[\d.,]+\S*) vs forecast$/, "$1 vs previsão"],
    [/^→ revised (.+)$/, "→ revisado $1"],
    [/^What happens on (\d{2}\/\d{2}\/\d{4})$/, "O que acontece em $1"],
    [/^· (\S+) (\S+) only$/, "· só $1 $2"],
    [/^Nothing above low impact for (\S+) this day\.$/, "Nada acima de impacto baixo para $1 neste dia."],
    [/^\+(\d+)$/, "+$1"],
    [/^(January|February|March|April|May|June|July|August|September|October|November|December) (\d{4})$/,
      (m, mes, ano) => MESES[mes] + " de " + ano],
    [/^data (\d{2}\/\d{2} \d{2}:\d{2}) BRT$/, "dados $1 BRT"],
    [/^data (\d+) min old$/, "dados de $1 min"],
    [/^data (\d+)h old$/, "dados de $1h"],
    [/^of (\d+)% · (\d) of (\d) dimensions$/, "de $1% · $2 de $3 dimensões"],
    [/^ceiling (\d+)% — (\d) of (\d) dimensions connected$/, "teto $1% — $2 de $3 dimensões ligadas"],
    [/^(▲|▼|—) (hike|hold|cut)$/, (m, s, d) => s + " " + ({ hike: "alta", hold: "manutenção", cut: "corte" })[d]],
    [/^(\d+) of (\d+) — (\d+) pairs \+ (\d+) USD-driven instruments \(gold, NQ, ES\)$/,
      "$1 de $2 — $3 pares + $4 instrumentos movidos pelo USD (ouro, NQ, ES)"],
    [/^(\d+) of (\d+) pairs$/, "$1 de $2 pares"],
    [/^(hawkish|dovish|mixed) by count$/, (m, x) => ({ hawkish: "hawkish", dovish: "dovish", mixed: "misto" })[x] + " por contagem"],
    [/^(\d+)h \/ (\d+)d$/, "$1h / $2d"],
    // a nota do par: "<b>Long EUR/GBP</b> reads from the two legs: EUR leaning to <b>hike</b>
    // (50%) against GBP leaning to <b>hold</b> (50%) — a media divergence of 2 degrees. The
    // reason sits on <b>EUR</b>." — cada pedaco entre tags e um no
    [/^(Long|Short) (\S+)$/, (m, ls, par) => (ls === "Long" ? "Comprado em " : "Vendido em ") + par],
    [/^reads from the two legs: (\S+) leaning to (hike|hold|cut) \(score ([+\-−]?[\d.]+)\) against (\S+) leaning to (hike|hold|cut) \(score ([+\-−]?[\d.]+)\) — edge ([+\-−]?[\d.]+) of a possible 2\.00\.\s*(The reason sits on|Both legs carry the reason\.)?$/,
      (m, b, db, sb, q, dq, sq, e, cauda) => {
        const D = { hike: "alta", hold: "manutenção", cut: "corte" };
        return "lê pelas duas pernas: " + b + " inclinado a " + D[db] + " (score " + sb + ") contra " + q +
          " inclinado a " + D[dq] + " (score " + sq + ") — vantagem " + e + " de um máximo de 2,00." +
          (cauda === "The reason sits on" ? " A razão está em" : cauda ? " As duas pernas carregam a razão." : "");
      }],
    [/^The two legs score the same \((\S+) ([+\-−]?[\d.]+), (\S+) ([+\-−]?[\d.]+)\) — no edge between them on this axis\.$/,
      "As duas pernas têm o mesmo score ($1 $2, $3 $4) — sem vantagem entre elas neste eixo."],
    [/^\((\d+)% of a (\d+)% ceiling; score ([+\-−]?[\d.]+)\)\.\s*(.*)$/, (m, a, b, sc, cauda) => {
      const t = cauda ? traduz(cauda) : null;
      return "(" + a + "% de um teto de " + b + "%; score " + sc + ")." + (cauda ? " " + (t === null ? cauda : t.trim()) : "");
    }],
    [/^reads from the two legs: (\S+) leaning to$/, "lê pelas duas pernas: $1 inclinado a"],
    [/^\((\d+)%\) against (\S+) leaning to$/, "($1%) contra $2 inclinado a"],
    [/^\((\d+)%\) — a (fraca|media|forte|muito forte) divergence of (\d+) degrees?\.\s*(The reason sits on|Both legs carry the reason\.)?$/,
      (m, pct, r, n, cauda) => "(" + pct + "%) — uma divergência " +
        ({ fraca: "fraca", media: "média", forte: "forte", "muito forte": "muito forte" })[r] +
        " de " + n + " grau" + (n === "1" ? "" : "s") + "." +
        (cauda === "The reason sits on" ? " A razão está em" : cauda ? " As duas pernas carregam a razão." : "")],
    [/^Same bet as (.+?) — holding two does not diversify, it doubles\.$/,
      "Mesma aposta que $1 — segurar dois não diversifica, dobra."],
    [/^leaning to\s*$/, "inclinado a"],
    [/^\((\d+)%\) against\s*$/, "($1%) contra"],
    [/^\((\d+)%\) —\s*$/, "($1%) —"],
    [/^a (fraca|media|forte|muito forte) divergence of (\d+) degrees?\.\s*$/,
      (m, r, n) => "uma divergência " + ({ fraca: "fraca", media: "média", forte: "forte", "muito forte": "muito forte" })[r] + " de " + n + " grau" + (n === "1" ? "" : "s") + "."],
    [/^(.+?) is read through\s*$/, (m, nome) => ({ Gold: "Ouro" }[nome] || nome) + " é lido por"],
    [/^(.+?) is read from\s*$/, (m, nome) => ({ Gold: "Ouro" }[nome] || nome) + " é lido por"],
    [/^two legs$/, "duas pernas"],
    [/^: the US dollar's rate reading, inverted \(USD leaning to (hike|hold|cut), score ([+\-−]?[\d.]+) → ([+\-−]?[\d.]+) for (.+?)\), plus\s*$/,
      (m, dirr, s1, s2, nome) => ": a leitura de juro do dólar, invertida (USD inclinado a " + ({ hike: "alta", hold: "manutenção", cut: "corte" })[dirr] +
        ", score " + s1 + " → " + s2 + " para " + ({ Gold: "Ouro" }[nome] || nome) + "), mais"],
    [/^geopolitics$/, "geopolítica"],
    [/^\((not connected|quiet \(z [+\-−]?[\d.]+\)|conflict spike z [+\-−]?[\d.]+) → ([+\-−]?[\d.]+)\)\. Score ([+\-−]?[\d.]+) of a possible ([\d.]+) →\s*$/,
      (m, est, g, s, mx) => "(" + est.replace("not connected", "não conectada").replace("quiet", "quieta").replace("conflict spike", "pico de conflito") +
        " → " + g + "). Score " + s + " de um máximo de " + mx + " →"],
    [/^The two legs cancel out exactly today\.$/, "As duas pernas se cancelam exatamente hoje."],
    [/^one leg only — the US dollar$/, "uma perna só — o dólar americano"],
    [/^, which is leaning to\s*$/, ", que está inclinado a"],
    [/^\((\d+)% of a (\d+)% ceiling\)\.\s*(.*)$/, (m, a, b, cauda) => {
      const t = cauda ? traduz(cauda) : null;
      return "(" + a + "% de um teto de " + b + "%)." + (cauda ? " " + (t === null ? cauda : t.trim()) : "");
    }],
    [/^5 years of daily data, non-overlapping blocks: 10y real yield (\S+) same day, (\S+) over 20 sessions \(n=(\d+)\), (\S+) over 60 sessions \(n=(\d+)\); 2y nominal (\S+) over 60 sessions\. Predictive \(rates today → price tomorrow \/ next 5 days\): (\S+) \/ (\S+) — inside noise\. Micro contract tracks the big one at (\S+)\.$/,
      "5 anos de dados diários, blocos sem sobreposição: juro real 10a $1 no mesmo dia, $2 em 20 pregões (n=$3), $4 em 60 pregões (n=$5); 2a nominal $6 em 60 pregões. Preditiva (juro hoje → preço amanhã / 5 dias seguintes): $7 / $8 — dentro do ruído. O micro acompanha o contrato grande em $9."],
    [/^last move (\d{4}-\d{2}-\d{2}) \((.+?)\)$/, "último movimento $1 ($2)"],
    [/^· last move (.+)$/, "· último movimento $1"],
    [/^— (\d+) months? back$/, (m, n) => "— " + n + (n === "1" ? " mês" : " meses") + " atrás"],
    [/^\. That is the month that ended, not a delivery delay; every terminal has the same lag\.\s*$/,
      ". É o mês que acabou, não atraso de entrega; todo terminal tem a mesma defasagem."],
    [/^release → calendar source, measured per event: high-impact prints (.+?) \(median\) — see each card; release → BLS API: not timed yet, needs the registered key$/,
      "release → fonte do calendário, medida por evento: dados de alto impacto em $1 (mediana) — veja cada ficha; release → API do BLS: ainda não cronometrada, exige a chave registrada"],
    [/^\(\s*$/, "("],
    [/^(conflict|energy)\s*$/, (m, t) => ({ conflict: "conflito", energy: "energia" })[t]],
    [/^(conflict|energy) —$/, (m, t) => ({ conflict: "conflito", energy: "energia" })[t] + " —"],
    [/^tone ([+\-−]?[\d.]+)$/, "tom $1"],
    [/^risk-off: safe-haven flow tends to SUPPORT (\S+) \(rule\)$/, "risk-off: fluxo de refúgio tende a SUSTENTAR $1 (regra)"],
    [/^risk-off: risk currencies tend to LOSE — (\S+) \(rule\)$/, "risk-off: moedas de risco tendem a PERDER — $1 (regra)"],
    [/^risk-off: mixed for (\S+) \(rule\)$/, "risk-off: misto para $1 (regra)"],
    [/^energy shock: importer — inflation push, leans TIGHTENING \(rule\)$/, "choque de energia: importador — empurrão de inflação, pende a APERTO (regra)"],
    [/^energy shock: exporter — terms of trade up, inflation up; mixed for the rate \(rule\)$/, "choque de energia: exportador — termos de troca sobem, inflação sobe; misto para o juro (regra)"],
  ];

  // Fragmento que comeca com travessao ("— pushes toward TIGHTENING"): traduz o resto.
  // E o formato da linha de leitura da ficha, onde a classe vem em <strong> e o texto do
  // empurrao fica no mesmo no que o travessao.
  REGEX.push([/^— (.+)$/, (m, resto) => {
    const t = traduz(resto);
    return "— " + (t === null ? resto : t.trim());
  }]);

  function traduz(texto) {
    // espacos internos normalizados: os templates quebram linha no meio das frases, e a
    // chave do dicionario tem espaco simples
    const k = texto.replace(/\s+/g, " ").trim();
    if (!k) return null;
    const antes = (texto.match(/^\s*/) || [""])[0];
    const depois = (texto.match(/\s*$/) || [""])[0];
    if (Object.prototype.hasOwnProperty.call(EXATO, k)) {
      return EXATO[k] === k ? null : antes + EXATO[k] + depois;
    }
    for (const [re, sub] of REGEX) {
      if (re.test(k)) {
        const novo = k.replace(re, sub);
        return novo === k ? null : antes + novo + depois;
      }
    }
    return null;
  }

  function aplica(raiz) {
    if (!raiz) return;
    const nos = [];
    if (raiz.nodeType === 3) nos.push(raiz);
    else if (raiz.nodeType === 1 || raiz.nodeType === 9 || raiz.nodeType === 11) {
      const w = document.createTreeWalker(raiz, NodeFilter.SHOW_TEXT, {
        acceptNode: (n) => {
          const p = n.parentNode;
          if (!p) return NodeFilter.FILTER_REJECT;
          const tag = p.nodeName;
          if (tag === "SCRIPT" || tag === "STYLE" || tag === "CODE" || tag === "PRE") return NodeFilter.FILTER_REJECT;
          if (p.closest && p.closest("[translate=no], blockquote, .mac-fala-frase, .mac-fala-link")) return NodeFilter.FILTER_REJECT;
          return NodeFilter.FILTER_ACCEPT;
        },
      });
      let n;
      while ((n = w.nextNode())) nos.push(n);
    }
    let trocados = 0;
    for (const n of nos) {
      const t = traduz(n.nodeValue);
      if (t !== null && t !== n.nodeValue) { n.nodeValue = t; trocados++; }
    }
    return trocados;
  }

  /* ------------------------------------------------------------------ SELETOR */
  function seletor(idioma) {
    if (document.getElementById("macLang")) return;
    const ref = document.getElementById("updateButton");
    if (!ref || !ref.parentNode) return;
    const b = document.createElement("button");
    b.type = "button";
    b.id = "macLang";
    b.className = "mac-lang";
    b.setAttribute("translate", "no");
    b.title = idioma === "pt" ? "Switch to English" : "Mudar para português";
    b.innerHTML = idioma === "pt"
      ? '<b>PT</b><span>·</span>EN'
      : 'PT<span>·</span><b>EN</b>';
    b.addEventListener("click", () => {
      try { localStorage.setItem("mac_lang", idioma === "pt" ? "en" : "pt"); } catch (e) { /* ignora */ }
      location.reload();
    });
    ref.parentNode.insertBefore(b, ref.nextSibling);
  }

  const estilo = document.createElement("style");
  estilo.textContent = `
    .mac-lang{margin-left:8px;background:rgba(255,255,255,.06);border:1px solid rgba(255,255,255,.14);
      color:inherit;border-radius:7px;padding:5px 10px;cursor:pointer;font-size:12px;letter-spacing:.06em;
      font-family:var(--font-mono, monospace)}
    .mac-lang span{opacity:.35;margin:0 5px}
    .mac-lang b{color:var(--accent, #5eead4)}
    .mac-lang:hover{background:rgba(255,255,255,.12)}`;
  document.head.appendChild(estilo);

  /* ------------------------------------------------------------------ ARRANQUE */
  const idioma = idiomaAtual();
  window.__macIdioma = { idioma, aplica, traduz };
  document.documentElement.lang = idioma === "pt" ? "pt-BR" : "en";

  function arranca() {
    seletor(idioma);
    if (idioma !== "pt") return;
    aplica(document.body);

    // Reaplica a cada redesenho — trocas de aba, cliques em par, dias do calendario.
    // Primeira versao processava so os nos do lote e DESLIGAVA o observador durante a
    // aplicacao: lotes que chegavam no meio se perdiam, e o calendario ficava em ingles.
    // Agora: varredura COMPLETA do body, com debounce, sem desligar. E idempotente (texto ja
    // em portugues nao casa chave nenhuma) e custa poucos milissegundos.
    let agendado = null, aplicando = false;
    const conta = { observador: 0, varreduras: 0, trocados: 0, erro: null };
    const varre = () => {
      if (aplicando) return;
      aplicando = true;
      conta.varreduras++;
      try { conta.trocados += aplica(document.body) || 0; }
      catch (e) { conta.erro = e.message; }
      finally { aplicando = false; }
    };
    const obs = new MutationObserver(() => {
      conta.observador++;
      if (aplicando || agendado) return;
      agendado = setTimeout(() => { agendado = null; varre(); }, 60);
    });
    window.__macIdioma.conta = conta;
    obs.observe(document.body, { childList: true, subtree: true, characterData: true });
    // cliques redesenham; um tique depois, varre — mesmo que o observador ja tenha corrido
    document.addEventListener("click", () => setTimeout(varre, 120), true);
    // e passadas de seguranca no arranque, enquanto os JSONs chegam
    [800, 2500, 5000, 9000].forEach((ms) => setTimeout(varre, ms));
  }

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", arranca);
  else arranca();

})();
