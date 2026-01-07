import os
from typing import Optional

try:
    from neo4j import GraphDatabase
except Exception:  # pragma: no cover - optional dependency during early dev
    GraphDatabase = None


def get_neo4j_driver():
    if GraphDatabase is None:
        return None
    uri = os.getenv("NEO4J_URI", "bolt://neo4j:7687")
    auth = os.getenv("NEO4J_AUTH", "neo4j/test").split("/")
    user = auth[0]
    pwd = auth[1] if len(auth) > 1 else "test"
    return GraphDatabase.driver(uri, auth=(user, pwd))
