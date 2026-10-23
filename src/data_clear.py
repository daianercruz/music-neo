import pandas as pd

info = pd.read_csv("Music Info.csv")


df = info[["track_id", "name", "artist", "tags", "genre", "year"]].dropna().copy()
df = df.drop_duplicates("track_id")


for c in ["name", "artist", "genre"]:
    df[c] = df[c].str.strip()

def limpar_tags(t):
    vistos = []
    for x in str(t).lower().split(","):
        x = x.strip()
        if x and x not in vistos:
            vistos.append(x)
    return vistos

df["tag_list"] = df["tags"].apply(limpar_tags)
df["tags"] = df["tag_list"].str.join(", ")


df["year"] = df["year"].astype(int)
df["decade"] = df["year"] // 10 * 10


freq = pd.Series([t for l in df["tag_list"] for t in l]).value_counts()
comuns = set(freq.head(40).index)

def nicho(lista, genero):
    for t in lista:
        if t in comuns and t != genero.lower():
            return t
    return "outros"

df["niche"] = [nicho(l, g) for l, g in zip(df["tag_list"], df["genre"])]


out = df.rename(columns={"track_id": "song_id", "name": "title"})
out[["song_id", "title", "artist", "tags", "genre", "year", "decade", "niche"]] \
    .to_csv("musicas.csv", index=False)

print(len(out), "músicas exportadas")
print("anos:", out["year"].min(), "a", out["year"].max())
print(out["genre"].value_counts())
print(out["niche"].value_counts().head(15))