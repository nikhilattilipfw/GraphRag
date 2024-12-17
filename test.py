from neo4j import GraphDatabase
import os
from dotenv import load_dotenv
import openai
from openai import OpenAI
import PyPDF2

load_dotenv()

# Neo4j connection details
neo4j_uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
neo4j_user = os.getenv("NEO4J_USER", "neo4j")
neo4j_password = os.getenv("NEO4J_PASSWORD", "your-fallback-password")

# Initialize the Neo4j driver
driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_password))

def get_all_entity_names():
    """
    Fetch all entity names from the Neo4j database.
    """
    query = """
    MATCH (e:Entity)
    RETURN e.type AS name
    """
    entity_names = []
    with driver.session() as session:
        result = session.run(query)
        print(result.data())
        # Collect all names into a list
        entity_names = [record["name"] for record in result if "name" in record]
    return entity_names


# Example usage
entities = get_all_entity_names()
print("Retrieved entities:", entities)


driver.close()
