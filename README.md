Here's a detailed **README** file for your project:

---

# Second Brain Knowledge Base

## Description

**Second Brain Knowledge Base** is a Streamlit-based application that allows users to upload documents (PDFs or text files) and create a knowledge graph in Neo4j by extracting entities and relationships from the content. The project leverages OpenAI's GPT API for entity and relationship extraction and integrates Diffbot for data enrichment. Users can interact with the knowledge base through a chatbot interface that provides responses based on the ingested data.

---

## Features

1. **Document Ingestion**:
   - Upload PDF or text files.
   - Extract entities and relationships using OpenAI's GPT-3.5 Turbo model.
   - Enrich entity data using the Diffbot API.
   - Store data in a Neo4j graph database.

2. **Interactive Chatbot**:
   - Select a document to serve as context.
   - Ask questions and receive detailed answers based on the ingested data.
   - Dynamic chat history to enhance user experience.

3. **Neo4j Integration**:
   - Store entities, relationships, and document data.
   - Query the graph for relationships and provide contextual answers.

---

## Technology Stack

- **Python**: Core language for backend logic.
- **Streamlit**: User interface for document ingestion and chatbot interaction.
- **OpenAI GPT-3.5 Turbo**: Entity extraction and chatbot responses.
- **Neo4j**: Graph database for knowledge storage and query.
- **Diffbot**: Data enrichment service for entities.
- **PyPDF2**: PDF processing library.
- **dotenv**: Environment variable management.
- **Requests**: API calls to Diffbot and other services.

---

## Prerequisites

- Python 3.8 or higher
- Neo4j Database (with credentials)
- OpenAI API Key
- Diffbot API Token

---

## Installation

1. **Clone the Repository**:
   ```bash
   git clone <repository-url>
   cd <project-directory>
   ```

2. **Create a Virtual Environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Set Environment Variables**:
   Create a `.env` file and add the following:
   ```env
   OPENAI_API_KEY=your_openai_api_key
   NEO4J_URI=bolt://localhost:7687
   NEO4J_USER=your_neo4j_username
   NEO4J_PASSWORD=your_neo4j_password
   DIFFBOT_API_TOKEN=your_diffbot_api_token
   ```

5. **Start Neo4j Database**:
   Ensure your Neo4j server is running.

6. **Run the Application**:
   ```bash
   streamlit run <script_name>.py
   ```

---

## Usage

1. **Upload Documents**:
   - Go to the **Document Upload** tab.
   - Upload a PDF or text file.
   - Wait for the document to be processed and stored in the knowledge graph.

2. **Interact with the Chatbot**:
   - Navigate to the **Chatbot** tab.
   - Select a document to serve as context.
   - Ask questions, and the chatbot will provide relevant responses based on the document data.

---

## Neo4j Graph Schema

The following entities and relationships are created:

- **Entities**:
  - `Entity` nodes with properties like `text`, `type`, and enriched fields.
  - `Document` nodes with `title` and `content`.

- **Relationships**:
  - `CONTAINS`: Links a `Document` to its `Entity`.
  - `RELATES_TO`: Represents relationships between `Entity` nodes.

---

## Example Workflow

1. Upload a document titled `example.pdf`.
2. The app extracts entities and relationships:
   ```json
   {
       "entities": [
           {"type": "Person", "text": "John Doe"},
           {"type": "Organization", "text": "OpenAI"}
       ],
       "relationships": [
           {"source": "John Doe", "relation": "works_at", "target": "OpenAI"}
       ]
   }
   ```
3. The data is enriched using Diffbot and stored in Neo4j.
4. Query the chatbot:
   ```
   User: Who works at OpenAI?
   Chatbot: John Doe works at OpenAI.
   ```

---

## Future Improvements

- Add more data enrichment sources.
- Enhance chatbot response formatting.
- Integrate support for additional document types.

--- 
