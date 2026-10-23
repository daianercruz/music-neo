import pandas as pd

N = 50   

musicas = pd.read_csv("musicas.csv")
hist = pd.read_csv("User Listening History.csv") 

h = hist[hist["track_id"].isin(musicas["song_id"])]
pop = h.groupby("track_id")["user_id"].nunique()
top = pop.nlargest(N).index

musicas = musicas[musicas["song_id"].isin(top)]
musicas.to_csv("musicas_100.csv", index=False)
print(len(musicas), "músicas")
print(musicas["genre"].value_counts())