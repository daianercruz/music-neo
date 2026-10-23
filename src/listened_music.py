import pandas as pd

ARQUIVO_MUSICAS = "musicas_50.csv"   

musicas = pd.read_csv(ARQUIVO_MUSICAS)
usuarios = pd.read_csv("usuarios.csv")
hist = pd.read_csv("User Listening History.csv")  

h = hist[hist["track_id"].isin(musicas["song_id"])]
qtd = h.groupby("user_id")["track_id"].nunique()
elegiveis = qtd[(qtd >= 5) & (qtd <= 20)].index
print(len(elegiveis), "usuários elegíveis")          

reais = pd.Series(elegiveis).sample(50, random_state=42).tolist()
mapa = dict(zip(reais, usuarios["user_id"]))         

l = h[h["user_id"].isin(mapa)].copy()
l["user_id"] = l["user_id"].map(mapa)
l = l.rename(columns={"track_id": "song_id", "playcount": "vezes"})
l[["user_id", "song_id", "vezes"]].to_csv("listened.csv", index=False)
print(len(l), "relações LISTENED")