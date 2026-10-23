import csv
import os
import re
from pathlib import Path
from collections import defaultdict
from itertools import combinations

from dotenv import load_dotenv
from neo4j import GraphDatabase


load_dotenv()

URI = "NEO4J_URI"
AUTH = ("neo4j", "SUA_SENHA_ATUAL")

BANCO = os.getenv("NEO4J_DATABASE") or None

ARQUIVO_CSV = Path(__file__).parent / "musicas_50.csv"

SIMILARIDADE_MINIMA = 0.20
TAMANHO_LOTE = 500



if not URI:
    raise ValueError(
        "A variável NEO4J_URI não foi encontrada no arquivo .env."
    )

if not AUTH[0] or not AUTH[1]:
    raise ValueError(
        "A variável NEO4J_PASSWORD não foi encontrada no arquivo .env."
    )

if not ARQUIVO_CSV.exists():
    raise FileNotFoundError(
        f"Arquivo CSV não encontrado: {ARQUIVO_CSV}"
    )



def normalizar_tags(valor):
    """
    Converte as tags de uma música em um conjunto.
    Aceita tags separadas por vírgula, ponto e vírgula ou pipe.
    """

    if not valor:
        return set()

    tags = re.split(r"[,;|]", str(valor).lower())

    return {
        tag.strip()
        for tag in tags
        if tag.strip()
    }


def calcular_jaccard(tags_a, tags_b):
    """
    Calcula a similaridade entre dois conjuntos de tags.

    Jaccard = interseção / união
    """

    if not tags_a or not tags_b:
        return 0.0

    intersecao = tags_a.intersection(tags_b)
    uniao = tags_a.union(tags_b)

    return len(intersecao) / len(uniao)


def carregar_musicas():
    musicas = []

    with open(
        ARQUIVO_CSV,
        mode="r",
        encoding="utf-8-sig",
        newline=""
    ) as arquivo:

        leitor = csv.DictReader(arquivo)

        colunas_obrigatorias = {"song_id", "tags"}

        if not leitor.fieldnames:
            raise ValueError("O CSV está vazio ou não possui cabeçalho.")

        faltantes = colunas_obrigatorias - set(leitor.fieldnames)

        if faltantes:
            raise ValueError(
                f"Colunas ausentes no CSV: {', '.join(faltantes)}"
            )

        for linha in leitor:
            song_id = (linha.get("song_id") or "").strip()

            if not song_id:
                continue

            tags = normalizar_tags(linha.get("tags"))

            if not tags:
                continue

            musicas.append({
                "song_id": song_id,
                "title": linha.get("title", ""),
                "tags": tags
            })


    ids = [musica["song_id"] for musica in musicas]

    if len(ids) != len(set(ids)):
        raise ValueError(
            "O CSV contém song_id duplicados. "
            "Corrija os IDs antes de calcular a similaridade."
        )

    print(f"Músicas carregadas: {len(musicas)}")

    return musicas


def gerar_similaridades(musicas):
    """
    Compara músicas que possuem pelo menos uma tag em comum.
    Retorna os pares que atingem a similaridade mínima.
    """

    indice_tags = defaultdict(list)

    for indice, musica in enumerate(musicas):
        for tag in musica["tags"]:
            indice_tags[tag].append(indice)

    pares_candidatos = set()

    for indices in indice_tags.values():
        for indice_a, indice_b in combinations(indices, 2):
            pares_candidatos.add((indice_a, indice_b))

    print(f"Relacionamentos candidatos: {len(pares_candidatos)}")

    similares = []

    for indice_a, indice_b in pares_candidatos:
        musica_a = musicas[indice_a]
        musica_b = musicas[indice_b]

        score = calcular_jaccard(
            musica_a["tags"],
            musica_b["tags"]
        )

        if score >= SIMILARIDADE_MINIMA:
            similares.append({
                "id_a": musica_a["song_id"],
                "id_b": musica_b["song_id"],
                "similaridade": round(score, 4)
            })

    similares.sort(
        key=lambda item: item["similaridade"],
        reverse=True
    )

    print(
        f"Relacionamentos com similaridade >= "
        f"{SIMILARIDADE_MINIMA}: {len(similares)}"
    )

    return similares


def salvar_similaridades(driver, similares):
    """
    Cria relações SIMILAR_TO entre músicas já existentes no banco.

    O uso de toString permite comparar IDs mesmo quando eles
    foram armazenados como números no Neo4j e lidos como texto no CSV.
    """

    if not similares:
        print("Nenhuma similaridade encontrada para salvar.")
        return

    query = """
    UNWIND $pares AS p

    MATCH (a:Song)
    WHERE toString(a.song_id) = p.id_a

    WITH a, p

    MATCH (b:Song)
    WHERE toString(b.song_id) = p.id_b
      AND elementId(a) <> elementId(b)

    MERGE (a)-[r:SIMILAR_TO]-(b)

    SET r.score = p.similaridade

    RETURN count(r) AS gravadas
    """

    total_processado = 0
    total_gravado = 0

    # BANCO=None permite que o driver utilize o banco padrão.
    with driver.session(database=BANCO) as session:

        for inicio in range(0, len(similares), TAMANHO_LOTE):
            lote = similares[inicio:inicio + TAMANHO_LOTE]

            resultado = session.run(
                query,
                pares=lote
            ).single()

            gravadas = resultado["gravadas"] if resultado else 0

            total_processado += len(lote)
            total_gravado += gravadas

            print(
                f"Lote processado: {total_processado}/"
                f"{len(similares)}"
            )

    print("\nProcessamento finalizado!")
    print(f"Pares calculados: {len(similares)}")
    print(f"Registros de relacionamento processados: {total_gravado}")



def main():
    driver = None

    try:
        print("Carregando músicas...")
        musicas = carregar_musicas()

        print("\nCalculando similaridades...")
        similares = gerar_similaridades(musicas)

        print("\nConectando ao Neo4j Aura...")

        driver = GraphDatabase.driver(URI, auth=AUTH)
        

        driver.verify_connectivity()

        print("Conexão estabelecida!")

        print("\nSalvando relacionamentos...")
        salvar_similaridades(driver, similares)

    except Exception as erro:
        print(f"\nErro durante a execução: {erro}")
        raise

    finally:
        if driver is not None:
            driver.close()
            print("\nConexão encerrada.")


if __name__ == "__main__":
    main()