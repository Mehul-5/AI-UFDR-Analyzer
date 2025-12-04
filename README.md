**🕵️‍♂️ AI-Powered UFDR Forensic Analyzer**

A local-first Digital Forensics platform that combines Retrieval-Augmented Generation (RAG) with Knowledge Graphs to analyze mobile extraction reports (.ufdr) without cloud data leakage.

![Image](https://github.com/user-attachments/assets/b5bf4595-e389-42e1-81a8-3de35f01532f)

---

**🚀 Why This Exists**

Traditional forensic tools (like Cellebrite Reader) rely heavily on manual keyword searches. If an investigator searches for "drugs," they miss messages like "bring the stuff" or "is the package ready?"

This tool solves that gap.
By ingesting UFDR dumps into a local Vector Database (Qdrant) and a Knowledge Graph (Neo4j), it allows investigators to ask semantic questions like "Show me suspicious financial discussions" and get relevant results regardless of the specific keywords used.

Privacy First: All data processing happens locally via Docker containers. The only external call is to the LLM (Gemini) for summarization, with PII redaction capabilities.

---

**🏗️ System Architecture**

![image alt](https://raw.githubusercontent.com/Mehul-5/AI-UFDR-Analyzer/refs/heads/main/Architecture.png)

The system follows a modern **RAG (Retrieval-Augmented Generation)** pipeline:


### 1. **Ingestion Engine (`/parsers`)**

- A modular Python parser streams the **`.ufdr` (ZIP)** file.
- It dynamically detects and extracts **SQLite databases (`mmssms.db`, `calllog.db`)** and **XML reports**.
- **Innovation:** Uses a schema-agnostic extraction algorithm to handle different device manufacturer formats automatically.


### 2. **Data Orchestration (`DataProcessor`)**

- **Structured Data:** Stored in **PostgreSQL** for exact filtering (dates, numbers).
- **Unstructured Data:** Chat messages are embedded (vectorized) using `BAAI/bge-large-en` and stored in **Qdrant**.
- **Relationships:** Contacts and calls are mapped as nodes/edges in **Neo4j** to visualize criminal networks.


### 3. *AI Analysis (`AIService`)*

- User queries (e.g., _"Find the drug dealer"_) are converted to vectors.
- The vector is matched against Qdrant to retrieve semantically relevant messages.
- Retrieved evidence is summarized using **Gemini 2.5 Flash** to provide investigative insights.

---

**🛠️ Tech Stack**

| Component   | Technology               | Purpose                                   |
|-------------|--------------------------|-------------------------------------------|
| Backend     | FastAPI (Python 3.10)    | High-performance Async API                |
| Frontend    | React.js + Mantine UI    | Responsive Investigator Dashboard         |
| Vector DB   | Qdrant                   | Semantic Search & Embeddings              |
| Graph DB    | Neo4j                    | Relationship Mapping & Visualization      |
| Primary DB  | PostgreSQL               | Structured Evidence Storage               |
| Cache       | Redis                    | Session Management & Query Caching        |
| AI Model    | Gemini 2.5 Flash         | Contextual Summarization                  |
| DevOps      | Docker Compose           | One-click local deployment                |

---

**⚡ Quick Start (Local Docker)**

**Prerequisites:** Docker Desktop installed and running.
### 1. **Clone the Repository**
```
git clone [https://github.com/Mehul-5/AI-UFDR-Analyzer.git](https://github.com/Mehul-5/AI-UFDR-Analyzer.git)
cd AI-UFDR-Analyzer
```


### 2. **Configure Environment** Create a `.env` file in the root directory:
```
# Database Config (Default Docker values)
POSTGRES_HOST=localhost
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres123

# Vector & Graph DB
QDRANT_URL=http://localhost:6333
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=neo4j123

# AI Configuration
GEMINI_API_KEY=your_actual_api_key_here
```


### 3. **Launch Infrastructure**
```
docker-compose up -d
```


### 4. **Run Backend & Frontend**
- **Backend**: `cd backend && python main.py` (Runs on port 8000).
- **Frontend**: `cd frontend && npm start` (Runs on port 3000).
   
### 5. **Access the Dashboard** Open `http://localhost:3000` and upload your `.ufdr` file.

---

**🧪 Testing**

The backend includes a comprehensive test suite using `pytest`.
```
cd backend
Pytest
```


Unit Tests: Validates the `ChatParser`, `CallParser`, and `ContactParser` logic.
Integration Tests: Mocks the AI and Database to verify API endpoints (`/upload`, `/query`).

---

**🔮 Future Roadmap**

- **Offline LLM Support**: Replace Gemini with Ollama (Llama 3) for 100% air-gapped analysis.
- **Audio Transcription**: Integrate Whisper for analyzing voice notes.
- **Image Analysis**: Use CLIP model to search images by content description.

---

**👨‍💻 Author**

**Mehul Dixit** Full Stack Developer | AI & Forensics Enthusiast LinkedIn
