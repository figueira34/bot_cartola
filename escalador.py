import pandas as pd
import requests
import json
import os

CONFIG_FILE = "orcamento.json"

def carregar_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    return {"orcamento": 100.00}

def salvar_config(cfg):
    with open(CONFIG_FILE, "w") as f:
        json.dump(cfg, f, indent=2)

url = 'https://api.cartola.globo.com/partidas'
url2 = 'https://api.cartola.globo.com/atletas/mercado'
resposta = requests.get(url)
dados = resposta.json()

resposta2 = requests.get(url2)
dados2 = resposta2.json()
atletas = pd.json_normalize(dados2['atletas'])

rodada = dados['rodada']
clubes = pd.json_normalize(dados['clubes'].values())
partidas = pd.json_normalize(dados['partidas'])

def calculate_score(results):
    mapping = {'d': 0, 'e': 1, 'v': 3}
    valid_results = [r for r in results if r.strip() in mapping]
    scores = [mapping[r] for r in valid_results]
    return sum(scores) / len(valid_results) if valid_results else 0

partidas['mandante_nota'] = partidas['aproveitamento_mandante'].apply(calculate_score)
partidas['visitante_nota'] = partidas['aproveitamento_visitante'].apply(calculate_score)

tabela = partidas.merge(
    clubes[['id', 'abreviacao']],
    left_on='clube_casa_id',
    right_on='id',
    how='left'
).rename(columns={'abreviacao': 'mandante_abreviacao'}).drop(columns=['id'])

tabela = tabela.merge(
    clubes[['id', 'abreviacao']],
    left_on='clube_visitante_id',
    right_on='id',
    how='left'
).rename(columns={'abreviacao': 'visitante_abreviacao'}).drop(columns=['id'])

tabela['dif_posicao'] = (tabela['clube_casa_posicao'] - tabela['clube_visitante_posicao']) * -1
tabela['dif_aproveitamento'] = tabela['mandante_nota'] - tabela['visitante_nota']

times = tabela[[
    'clube_casa_id',
    'mandante_abreviacao',
    'clube_visitante_id',
    'visitante_abreviacao',
    'dif_posicao',
    'dif_aproveitamento'
]].copy()

times.columns = [
    'ID Casa',
    'Casa',
    'ID Fora',
    'Fora',
    'Diferença Tabela',
    'Diferença Notas'
]

def filtrar_times(df, time_col, id_col, filtro_nota, filtro_tabela, sentido='maior'):
    if sentido == 'maior':
        cond = (df['Diferença Notas'] >= filtro_nota) | (df['Diferença Tabela'] > filtro_tabela)
    else:
        cond = (df['Diferença Notas'] <= filtro_nota) | (df['Diferença Tabela'] < filtro_tabela)
    return df[cond][[time_col, id_col, 'Diferença Tabela', 'Diferença Notas']].rename(columns={time_col: 'Time', id_col: 'Id'})

casa_final = filtrar_times(
    times, 'Casa', 'ID Casa',
    times[times['Diferença Notas'] > 0]['Diferença Notas'].mean(),
    times[times['Diferença Tabela'] > 0]['Diferença Tabela'].mean()
)

fora_final = filtrar_times(
    times, 'Fora', 'ID Fora',
    times[times['Diferença Notas'] < 0]['Diferença Notas'].mean(),
    times[times['Diferença Tabela'] < 0]['Diferença Tabela'].mean(),
    sentido='menor'
)

escalar = pd.concat([casa_final, fora_final], ignore_index=True)
escalar[['Diferença Notas', 'Diferença Tabela']] = escalar[['Diferença Notas', 'Diferença Tabela']].abs()

provaveis = atletas[atletas['status_id'] == 7]
jogadores = pd.merge(provaveis, escalar[['Id', 'Time', 'Diferença Notas', 'Diferença Tabela']], left_on='clube_id', right_on='Id').drop(columns='Id')
jogadores = jogadores[(jogadores['jogos_num'] > 1) | (jogadores['posicao_id'] == 6)]

jogadores = jogadores.drop_duplicates(subset='atleta_id')

def calcular_rank_ponderado(df, pesos):
    df = df.copy()
    ranks = df[['media_num', 'pontos_num', 'Diferença Notas', 'Diferença Tabela']].rank(method='min', ascending=False)
    df['Weighted Sum'] = (ranks * pd.Series(pesos)).sum(axis=1)
    return df

pesos = {
    'media_num': 0.75,
    'pontos_num': 0.02,
    'Diferença Notas': 0.15,
    'Diferença Tabela': 0.08
}

formacoes = {
    '4-3-3': {1:1, 2:2, 3:2, 4:3, 5:3},
    '4-4-2': {1:1, 2:2, 3:2, 4:4, 5:2},
    '3-4-3': {1:1, 2:0, 3:3, 4:4, 5:3},
    '3-5-2': {1:1, 2:0, 3:2, 4:5, 5:2},
    '4-5-1': {1:1, 2:2, 3:2, 4:5, 5:1},
    '5-3-2': {1:1, 2:2, 3:3, 4:3, 5:2},
    '5-4-1': {1:1, 2:2, 3:3, 4:4, 5:1}
}

config = carregar_config()
orcamento_total = config["orcamento"]

def escalar_time(formacao, jogadores, orcamento_total):
    posicoes = formacoes[formacao]
    tecnicos = jogadores[jogadores['posicao_id'] == 6]
    tecnico_mais_barato = tecnicos['preco_num'].min()
    orcamento_disponivel = orcamento_total - tecnico_mais_barato

    titulares = []
    orcamento_usado = 0

    for pos_id, qtd in posicoes.items():
        filtrado = jogadores[jogadores['posicao_id'] == pos_id]
        rankeado = calcular_rank_ponderado(filtrado, pesos).sort_values(by='Weighted Sum')
        count = 0
        for _, row in rankeado.iterrows():
            if count == qtd:
                break
            if orcamento_usado + row['preco_num'] <= orcamento_disponivel:
                titulares.append(row.to_dict())
                orcamento_usado += row['preco_num']
                count += 1

    if len(titulares) < 11:
        return None, None

    orcamento_restante = orcamento_total - orcamento_usado
    tecnicos_rank = calcular_rank_ponderado(tecnicos, pesos)
    tecnico_escolhido = None

    for _, row in tecnicos_rank.sort_values(by='Weighted Sum').iterrows():
        if row['preco_num'] <= orcamento_restante:
            tecnico_escolhido = row.to_dict()
            break

    if tecnico_escolhido:
        titulares.append(tecnico_escolhido)
        return titulares, orcamento_usado + tecnico_escolhido['preco_num']
    return None, None    

melhor_formacao = None
melhor_time = None
melhor_midia = 0

for formacao in formacoes.keys():
    time, custo = escalar_time(formacao, jogadores, orcamento_usado)
    if time:
        media_time = sum([j['media_num'] for j in time])
        if media_time > melhor_midia:
            melhor_midia = media_time
            melhor_time = time
            melhor_formacao = formacao

reserva_posicoes = {1: 1, 2: 1, 3: 1, 4: 1, 5: 1}
titulares_df = pd.DataFrame(melhor_time)
reserves = []

for pos_id in reserva_posicoes:
    candidatos = jogadores[jogadores['posicao_id'] == pos_id]
    titulares_na_pos = titulares_df[titulares_df['posicao_id'] == pos_id]
    if not titulares_na_pos.empty:
        preco_min = titulares_na_pos['preco_num'].min()
        candidatos = candidatos[candidatos['preco_num'] < preco_min]
        if not candidatos.empty:
            reserva = candidatos.nlargest(1, 'media_num').iloc[0].to_dict()
            reserves.append(reserva)

reserves_df = pd.DataFrame(reserves)

titulares_df['Reserva'] = 0
reserves_df['Reserva'] = 1
final_df = pd.concat([titulares_df, reserves_df])

final_df['posicao_id'] = final_df['posicao_id'].astype(int)
mapa_posicoes = {1: 'Goleiro', 2: 'Lateral', 3: 'Zagueiro', 4: 'Meia', 5: 'Atacante', 6: 'Técnico'}
final_df['Posição'] = final_df['posicao_id'].map(mapa_posicoes)

def selecionar_melhor(df):
    df = calcular_rank_ponderado(df, pesos)
    return df.loc[df['Weighted Sum'].idxmin(), 'apelido']

capitao = selecionar_melhor(titulares_df)
reserva_luxo = selecionar_melhor(reserves_df)

def definir_multiplicador(row):
    if row['Reserva'] == 0 and row['apelido'] == capitao:
        return 'Capitão'
    elif row['Reserva'] == 0:
        return 'Titular'
    elif row['apelido'] == reserva_luxo:
        return 'Reserva de Luxo'
    else:
        return 'Reserva'

final_df['Multiplicador'] = final_df.apply(definir_multiplicador, axis=1)

final_df = final_df.rename(columns={
    'atleta_id': 'Id Atleta',
    'apelido': 'Nome',
    'media_num': 'Média',
    'pontos_num': 'Última Rodada',
    'jogos_num': 'Jogos',
    'preco_num': 'Preço',
    'Time': 'Clube'
})

colunas_finais = ['Id Atleta', 'Posição', 'Nome', 'Média', 'Última Rodada', 'Jogos', 'Preço', 'Clube', 'Diferença Notas', 'Diferença Tabela', 'Multiplicador']
time = final_df[colunas_finais]

media_total = round(titulares_df['media_num'].sum(), 2)
preco_total = round(titulares_df['preco_num'].sum(), 2)
ultima_rodada = round(titulares_df['pontos_num'].sum(), 2)

TOKEN = os.environ["TELEGRAM_TOKEN"]
CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]

def enviar(msg):
    requests.post(
        f"https://api.telegram.org/bot{TOKEN}/sendMessage",
        data={"chat_id": CHAT_ID, "text": msg}
    )

mensagem = f"""
⚽ TIME SUGERIDO

Formação: {melhor_formacao}
Média Total: {media_total}
Preço Total: {preco_total}

Capitão: {capitao}
Reserva de Luxo: {reserva_luxo}

Time: {time}
"""

enviar(mensagem)

