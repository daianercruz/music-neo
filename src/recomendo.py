import os

from dotenv import load_dotenv
from neo4j import GraphDatabase


load_dotenv()

URI = "NEO4J_URI"
AUTH = ("neo4j", "SUA_SENHA_ATUAL")

BANCO = os.getenv("NEO4J_DATABASE") or None


QUERY_RECOMENDACAO = """
MATCH (a:Song)-[:IN_GENRE]->(g:Genre)<-[:IN_GENRE]-(b:Song)
WHERE elementId(a) < elementId(b)

WITH a, b, count(DISTINCT g) AS generos_em_comum

OPTIONAL MATCH (a)-[:IN_NICHE]->(n:Niche)<-[:IN_NICHE]-(b)

WITH
    a,
    b,
    generos_em_comum,
    count(DISTINCT n) AS nichos_em_comum

OPTIONAL MATCH (a)-[:FROM_ERA]->(e:Era)<-[:FROM_ERA]-(b)

WITH
    a,
    b,
    generos_em_comum,
    nichos_em_comum,
    count(DISTINCT e) AS epocas_em_comum

OPTIONAL MATCH (a)-[r:SIMILAR_TO]-(b)

WITH
    a,
    b,
    generos_em_comum,
    nichos_em_comum,
    epocas_em_comum,
    coalesce(max(r.score), 0.0) AS similaridade_tags

WITH
    a,
    b,
    generos_em_comum,
    nichos_em_comum,
    epocas_em_comum,
    similaridade_tags,
    (
        generos_em_comum * 3 +
        nichos_em_comum * 2 +
        epocas_em_comum +
        similaridade_tags * 5
    ) AS pontuacao

WHERE
    generos_em_comum > 0
    OR nichos_em_comum > 0
    OR epocas_em_comum > 0
    OR similaridade_tags > 0

RETURN
    a.title AS musica,
    b.title AS musica_recomendada,
    generos_em_comum,
    nichos_em_comum,
    epocas_em_comum,
    round(similaridade_tags * 100) / 100 AS similaridade_tags,
    pontuacao

ORDER BY pontuacao DESC

LIMIT $limite
"""


def recomendar_musicas(limite=50):

    if not URI or not AUTH[1]:
        raise ValueError(
            "Configure NEO4J_URI e NEO4J_PASSWORD no arquivo .env."
        )

    with GraphDatabase.driver(
        URI,
        auth=AUTH
    ) as driver:

        driver.verify_connectivity()

        with driver.session(database=BANCO) as session:

            resultado = session.run(
                QUERY_RECOMENDACAO,
                limite=limite
            )

            return [registro.data() for registro in resultado]



if __name__ == "__main__":

    try:
        recomendacoes = recomendar_musicas(limite=50)

        if not recomendacoes:
            print("Nenhuma recomendação encontrada.")

        else:
            print("\nRECOMENDAÇÕES MUSICAIS\n")

            for item in recomendacoes:

                print("-" * 50)

                print(f"Música original: {item['musica']}")
                print(
                    f"Música recomendada: "
                    f"{item['musica_recomendada']}"
                )

                print(
                    f"Gêneros em comum: "
                    f"{item['generos_em_comum']}"
                )

                print(
                    f"Nichos em comum: "
                    f"{item['nichos_em_comum']}"
                )

                print(
                    f"Épocas em comum: "
                    f"{item['epocas_em_comum']}"
                )

                print(
                    f"Similaridade das tags: "
                    f"{item['similaridade_tags']}"
                )

                print(
                    f"Pontuação: {item['pontuacao']}"
                )

    except Exception as erro:
        print(f"Erro ao gerar recomendações: {erro}")
