# Arquivos aposentados em 02/set/2026

Estes quatro estavam em `data/raw` sem nenhum script Python referenciando-os. Sobraram de uma
versao anterior do coletor, ninguem os atualizava, e a guarda de frescor — corretamente —
apontava que estavam vencidos.

    cad_boc_2y_2002.json        parado em 18/ago
    chf_snb_rendeiduebd.csv     parado em 03/ago
    chf_snb_rendoblid.csv       parado em 01/set/2025 (um ano)
    eur_bundesbank_2y.csv       parado em 19/ago

O efeito foi caro: a guarda roda com `--estrito`, entao ela FALHAVA a cadeia inteira. Entre
31/ago e 02/set foram **cinco execucoes seguidas reprovadas**, e o painel ficou tres dias sem
atualizar. Um alarme correto sobre dado que nao importava bloqueou o dado que importava.

As moedas que eles alimentariam continuam com serie fresca, de outra fonte:
    CAD -> cad_boc_2y.json       CHF -> chf_snb_nss_2y.csv       EUR -> eur_ecb_2y.csv

LICAO: guarda que derruba a cadeia precisa vigiar so o que a cadeia usa. Arquivo orfao vira
alarme permanente, e alarme permanente ou derruba tudo ou ensina a ignorar o alarme.
