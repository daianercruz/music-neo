from neo4j import GraphDatabase

URI = "NEO4J_URI"
AUTH = ("neo4j", "SUA_SENHA_ATUAL")

print("1. Iniciando o teste...", flush=True)

try:
    driver = GraphDatabase.driver(URI, auth=AUTH)

    print("2. Testando conexão...", flush=True)
    driver.verify_connectivity()

    print("3. Conexão estabelecida!", flush=True)

    with driver.session() as session:
        resultado = session.run("""
            MATCH (s:Song)
            RETURN count(s) AS total
        """)

        total = resultado.single()["total"]
        print(f"4. Músicas encontradas no banco: {total}", flush=True)

    driver.close()
    print("5. Teste concluído!", flush=True)

except Exception as erro:
    print(f"ERRO: {type(erro).__name__}: {erro}", flush=True)