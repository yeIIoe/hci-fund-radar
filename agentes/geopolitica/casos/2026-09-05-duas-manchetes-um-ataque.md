# Duas manchetes, um ataque — 05/set/2026

```
versao_prompt   geopolitica@v1 (caso herdado: o erro é anterior ao agente)
tipo            lápide de origem — ver LAPIDES.md, L1
```

## O que aconteceu

O painel mostrou ao dono **duas manchetes** de conflito. Ele leu as duas e viu que descreviam
**o mesmo ataque**, publicado por veículos diferentes. Duas linhas na tela, **um** evento no
mundo.

## Por que isso é grave, e não cosmético

1. **Dobra a intensidade aparente.** Volume é contagem de artigos: republicação vira "mais
   notícia" sem que nada tenha acontecido a mais.
2. **Falsifica a confirmação.** Duas fontes dizendo a mesma coisa parece corroboração. Não é:
   é um despacho e um eco.
3. **Contamina o julgamento.** Um agente que conta eventos acaba dizendo "escalada" onde há
   repetição.

## A correção, que já está na camada 1

`geopolitica.py` passou a entregar `manchetes_unicas`: uma linha por **evento**, com `fontes[]`,
`n_republicacoes`, `agrupadas[]` e `confiabilidade`. A régua está declarada em
`regra_deduplicacao`:

- **regra 1** — Jaccard ≥ 0,55 sobre as palavras de 4+ letras do título normalizado;
- **regra 2** — mesma classe de `acao` **e** Jaccard de entidades ≥ 0,60 **e** ≥ 2 entidades em
  comum;
- **representante** — a fonte de maior confiabilidade; empatando, a publicação mais antiga.

Em 07/set essa régua removeu **4 duplicatas** de 5 manchetes em `mundo.conflito`.

## Os buracos declarados — e o que sobra para você

A régua deduplica **de menos, nunca de mais** (decisão consciente: duplicata visível é preferível
a fusão errada). Dois buracos escritos no próprio arquivo:

- manchete sobre lugar fora do léxico de entidades não ganha assinatura e cai só na regra 1;
- evento com **uma** entidade só não agrupa, porque a regra 2 exige duas em comum.

**Sua obrigação:** se dois itens de `manchetes_unicas` forem o mesmo fato, **funda os dois no seu
julgamento**, cite os dois títulos no motivo e abra **um** julgamento. Nunca dois.

## A regra que fica

> **Republicação não é confirmação.** Conte **eventos**, nunca artigos. E quando citar
> `n_republicacoes`, diga ao lado quantas fontes **independentes** existem de fato.

## Desfecho

```
reincidencia    (a preencher: alguma rodada voltou a mostrar o mesmo fato em duas linhas?)
medido_em       (a preencher)
```
