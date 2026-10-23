import pandas as pd
from neo4j import GraphDatabase

ARQUIVO_MUSICAS = "musicas_50.csv"

URI = "NEO4J_URI"
AUTH = ("neo4j", "SUA_SENHA_ATUAL")


driver = GraphDatabase.driver(URI, auth=AUTH)
driver.verify_connectivity()
print("Conexão estabelecida com sucesso!")


constraints = [
    "CREATE CONSTRAINT song_id IF NOT EXISTS FOR (s:Song) REQUIRE s.song_id IS UNIQUE",
    "CREATE CONSTRAINT artist_name IF NOT EXISTS FOR (a:Artist) REQUIRE a.name IS UNIQUE",
    "CREATE CONSTRAINT genre_name IF NOT EXISTS FOR (g:Genre) REQUIRE g.name IS UNIQUE",
    "CREATE CONSTRAINT era_decade IF NOT EXISTS FOR (e:Era) REQUIRE e.decade IS UNIQUE",
    "CREATE CONSTRAINT niche_name IF NOT EXISTS FOR (n:Niche) REQUIRE n.name IS UNIQUE",
    "CREATE CONSTRAINT user_id IF NOT EXISTS FOR (u:User) REQUIRE u.user_id IS UNIQUE",
    "CREATE CONSTRAINT country_name IF NOT EXISTS FOR (c:Country) REQUIRE c.name IS UNIQUE",
    "CREATE CONSTRAINT age_group IF NOT EXISTS FOR (g:AgeGroup) REQUIRE g.name IS UNIQUE",
]
with driver.session() as s:
    for c in constraints:
        s.run(c)


def carregar(query, arquivo, lote=1000):
    recs = pd.read_csv(arquivo).to_dict("records")
    with driver.session() as s:
        for i in range(0, len(recs), lote):
            s.run(query, rows=recs[i:i + lote])

carregar("""
UNWIND $rows AS r
MERGE (s:Song {song_id: r.song_id})
  SET s.title = r.title, s.year = r.year, s.tags = r.tags
MERGE (a:Artist {name: r.artist})  MERGE (a)-[:PERFORMS]->(s)
MERGE (g:Genre {name: r.genre})    MERGE (s)-[:IN_GENRE]->(g)
MERGE (e:Era {decade: r.decade})   MERGE (s)-[:FROM_ERA]->(e)
MERGE (n:Niche {name: r.niche})    MERGE (s)-[:IN_NICHE]->(n)
""", ARQUIVO_MUSICAS)

carregar("""
UNWIND $rows AS r
MERGE (u:User {user_id: r.user_id}) SET u.nome = r.nome, u.idade = r.idade
MERGE (c:Country {name: r.nacionalidade})  MERGE (u)-[:FROM]->(c)
MERGE (ag:AgeGroup {name: r.faixa_etaria}) MERGE (u)-[:IN_AGE_GROUP]->(ag)
""", "usuarios.csv")

carregar("""
UNWIND $rows AS r
MATCH (u:User {user_id: r.user_id}), (s:Song {song_id: r.song_id})
MERGE (u)-[l:LISTENED]->(s) SET l.vezes = r.vezes
""", "listened.csv")


with driver.session() as s:
    print(s.run("MATCH (n) RETURN labels(n)[0] AS tipo, count(*) AS total").data())
    print(s.run("MATCH ()-[r]->() RETURN type(r) AS relacao, count(*) AS total").data())

driver.close()