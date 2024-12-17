import os
from openai import OpenAI
from neo4j import GraphDatabase
import streamlit as st
from dotenv import load_dotenv
import PyPDF2
import json

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

neo4j_uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
neo4j_user = os.getenv("NEO4J_USER", "neo4j")
neo4j_password = os.getenv("NEO4J_PASSWORD", "Graphrag123")

driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_password))


def openai_generate(prompt, response_format=None):
    try:
        params = {
            "model": "gpt-3.5-turbo",
            "messages": [
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt},
            ]
        }
        if response_format == "json":
            params["response_format"] = {"type": "json_object"}
        chat_completion = client.chat.completions.create(**params)
        return chat_completion.choices[0].message.content
    except Exception as e:
        st.error(f"Error generating response: {str(e)}")
        return None


def extract_entities_and_relations(text):
    prompt = f"""Extract entities and their relationships from this text: {text}
    Output the information in the following JSON format:

        {{
    "entities": [
        {{
        "type": "Entity_Type",
        "text": "Entity_Text",
        "data_fields": {{
            "Field1": "Value1",
            "Field2": "Value2"
        }}
        }}
        ],
    "relationships": [
            {{
            "source": "Entity1_Name",
            "relation": "Relationship_Type",
            "target": "Entity2_Name"
            }}
        ]
        }}
    """
    response = openai_generate(prompt, "json")
    print("Got the response", response)
    try:
        return response
    except json.JSONDecodeError as e:
        st.error(f"Error parsing OpenAI response: {str(e)}")
        return {}


import requests

DIFFBOT_ENHANCE_URL = "https://kg.diffbot.com/kg/v3/enhance"
DIFFBOT_API_TOKEN = "4f1770c8c988e67e3956a1bc44220036"


import urllib.parse


def flatten_diffbot_data(data):
    flattened_data = {}
    for key, value in data.items():
        if isinstance(value, dict):
            flattened_data[key] = json.dumps(value)
        elif isinstance(value, list):
            if all(isinstance(item, dict) for item in value):
                flattened_data[key] = json.dumps(value)
            else:
                flattened_data[key] = value
        else:
            flattened_data[key] = value
    return flattened_data


def query_diffbot(entity_text, entity_type="Entity"):
    try:
        if entity_type not in ["Person", "Organization"]:
            return None
        params = {
            "type": entity_type,
            "name": entity_text,
            "size": 1,
            "refresh": "false",
            "search": "false",
            "nonCanonicalFacts": "false",
            "jsonmode": "",
            "token": DIFFBOT_API_TOKEN,
        }
        query_url = f"{DIFFBOT_ENHANCE_URL}?{urllib.parse.urlencode(params)}"
        headers = {"accept": "application/json"}
        response = requests.get(query_url, headers=headers)
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Error querying Diffbot: {response.status_code} {response.text}")
            return None
    except Exception as e:
        st.error(f"Error querying Diffbot: {str(e)}")
        return None


def ingest_data_into_neo4j(doc_content, title):
    extracted_data = extract_entities_and_relations(doc_content)
    if not extracted_data:
        return
    extracted_data = json.loads(extracted_data)
    entities = extracted_data.get("entities", [])
    relationships = extracted_data.get("relationships", [])
    with driver.session() as session:
        try:
            session.run(
                "MERGE (doc:Document {title: $title}) SET doc.content = $content",
                title=title,
                content=doc_content,
            )
            for entity in entities:
                entity_type = entity.get("type", "Unknown")
                entity_text = entity.get("text", "")
                data_fields = entity.get("data_fields", {})
                diffbot_type = (
                    "Person" if entity_type.lower() == "person"
                    else "Organization" if entity_type.lower() == "organization"
                    else "Entity"
                )
                enriched_data = query_diffbot(entity_text, entity_type=diffbot_type)
                if enriched_data and "data" in enriched_data:
                    diffbot_fields = enriched_data["data"]
                    for field in diffbot_fields:
                        flattened_fields = flatten_diffbot_data(field)
                        data_fields.update(flattened_fields)
                query = """
                MERGE (e:Entity {text: $text})
                SET e.type = $type, e.name = $text
                """
                params = {"text": entity_text, "type": entity_type}
                for key, value in data_fields.items():
                    sanitized_key = key.replace(" ", "_")
                    query += f", e.`{sanitized_key}` = ${sanitized_key}"
                    params[sanitized_key] = value
                session.run(query, params)
                session.run(
                    """
                    MATCH (doc:Document {title: $title})
                    MATCH (e:Entity {text: $text})
                    MERGE (doc)-[:CONTAINS]->(e)
                    """,
                    title=title,
                    text=entity_text,
                )
            for relationship in relationships:
                source = relationship.get("source", "")
                relation = relationship.get("relation", "")
                target = relationship.get("target", "")
                if source and relation and target:
                    session.run(
                        """
                        MATCH (source:Entity {text: $source})
                        MATCH (target:Entity {text: $target})
                        MERGE (source)-[r:RELATES_TO {type: $relation}]->(target)
                        """,
                        source=source,
                        target=target,
                        relation=relation,
                    )
        except Exception as e:
            st.error(f"Error ingesting data into Neo4j: {str(e)}")


def process_and_ingest_document(file):
    title = file.name
    if file.type == "application/pdf":
        try:
            reader = PyPDF2.PdfReader(file)
            content = "".join([page.extract_text() for page in reader.pages])
            ingest_data_into_neo4j(content, title)
        except Exception as e:
            st.error(f"Error processing PDF: {str(e)}")
    elif file.type == "text/plain":
        try:
            content = file.read().decode("utf-8", errors="replace")
            ingest_data_into_neo4j(content, title)
        except Exception as e:
            st.error(f"Error processing text file: {str(e)}")
    else:
        st.error("Unsupported file format. Please upload a PDF or TXT file.")


def query_second_brain(question):
    prompt = f"""Extract entities from this question to query our knowledge base: {question}.
    Output in following JSON format:
    {{
        "Entities":[Entity 1, Entity 2, ...]"
    }}
    """
    response = openai_generate(prompt, "json")
    print("Got the response from question", response)
    if response:
        return response
    else:
        return []


def query_neo4j(extracted_info):
    query = """
    MATCH (e:Entity)
    WHERE toLower(e.type) = toLower($entity_text)
    OPTIONAL MATCH (e)-[:RELATES_TO]->(related:Entity)
    RETURN e.text AS text, e.type AS type,
           COLLECT(DISTINCT related.text) AS related_entities
    """
    result_data = []
    extracted_info = json.loads(extracted_info)
    print(extracted_info, type(extracted_info))
    try:
        with driver.session() as session:
            for entity_text in extracted_info["Entities"]:
                if isinstance(entity_text, dict):
                    entity_text = entity_text.get("text", "")
                entity_text = str(entity_text)
                print("Extracted entities", entity_text)
                result = session.run(query, entity_text=entity_text)
                result_data.extend(result.data())
                print(result_data)
        return result_data
    except Exception as e:
        st.error(f"Error querying Neo4j: {str(e)}")
        return []


def generate_final_response(question, neo4j_data):
    context = f"The user asked/said: {question}. Based on this, here might be the additional information from our database: {neo4j_data}."
    prompt = f"You are a class helping assistant. You need to talk to the students and if asked a question answer them with the provided context. Provide a detailed answer if asked a question based on this context: {context} /n Feel free to chat with the user based on their response."
    return openai_generate(prompt)


def get_documents_from_neo4j():
    query = "MATCH (doc:Document) RETURN doc.title AS title"
    try:
        with driver.session() as session:
            result = session.run(query)
            return [record["title"] for record in result]
    except Exception as e:
        st.error(f"Error fetching documents from Neo4j: {str(e)}")
        return []


def fetch_context_from_document(document_title):
    query = """
    MATCH (doc:Document {title: $title})-[:CONTAINS]->(e:Entity)
    OPTIONAL MATCH (e)-[r:RELATES_TO]->(related:Entity)
    RETURN e.text AS entity_text, e.type AS entity_type, 
           COLLECT(DISTINCT related.text) AS related_entities
    """
    try:
        with driver.session() as session:
            result = session.run(query, title=document_title)
            return result.data()
    except Exception as e:
        st.error(f"Error fetching context from Neo4j: {str(e)}")
        return []


def app_ui():
    st.title("Second Brain Knowledge Base")
    tabs = st.tabs(["Document Upload", "Chatbot"])
    with tabs[0]:
        st.subheader("Upload Documents to Build Knowledge Base")
        uploaded_file = st.file_uploader("Choose a document to upload", type=["txt", "pdf"])
        if uploaded_file is not None:
            process_and_ingest_document(uploaded_file)
            st.success(f"Document '{uploaded_file.name}' has been successfully ingested into the knowledge base.")
    with tabs[1]:
        st.markdown("### Chat with the Knowledge Base")
        document_list = get_documents_from_neo4j()
        if not document_list:
            st.warning("No documents found in the knowledge base. Please upload a document first.")
            return
        selected_document = st.selectbox("Select a document to provide context", document_list)
        if selected_document:
            st.markdown(f"**Selected Document:** {selected_document}")
            if "chat_history" not in st.session_state:
                st.session_state.chat_history = []
            chat_placeholder = st.container()
            input_placeholder = st.container()
            with chat_placeholder:
                for message in st.session_state.chat_history:
                    with st.chat_message(message["role"]):
                        st.markdown(message["content"])
            with input_placeholder:
                user_input = st.chat_input("Type your question and press Enter...")
            if user_input:
                st.session_state.chat_history.append({"role": "user", "content": user_input})
                with chat_placeholder:
                    with st.chat_message("assistant"):
                        thinking_message = st.markdown("Thinking...")
                try:
                    context_data = fetch_context_from_document(selected_document)
                    if context_data:
                        final_response = generate_final_response(user_input, context_data)
                    else:
                        final_response = openai_generate(
                            f"Answer the following question: {user_input}"
                        )
                    response = final_response or "I couldn't find a suitable answer."
                    thinking_message.markdown(response)
                    st.session_state.chat_history.append({"role": "assistant", "content": response})
                except Exception as e:
                    error_message = f"An error occurred: {str(e)}"
                    thinking_message.markdown(error_message)
                    st.session_state.chat_history.append({"role": "assistant", "content": error_message})


if __name__ == "__main__":
    app_ui()

driver.close()
