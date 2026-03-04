# ⚖️ LexGuard: Neuro-Symbolic Compliance Auditor
**Phase 6: Agentic System Integration**

[![Demo Video] - https://youtu.be/76Jq8XyKvWY

## 📖 Project Overview
LexGuard is an AI-powered compliance auditor designed to analyze coontracts and Lease Agreements. By utilizing a "Recall-Then-Reason" pipeline, LexGuard decouples document retrieval from logical reasoning. 

For this milestone, LexGuard has been upgraded with an autonomous Agent layer powered by **Gemini 2.5 Flash**. The agent can interpret user queries, iteratively select the appropriate Python tools, fetch raw contract clauses directly from a Snowflake data warehouse, and synthesize a final compliance verdict (e.g., identifying high-risk indemnification clauses).

## 🧠 System Workflow
1. **User Interaction:** The user submits a natural language query via the Streamlit chat interface.
2. **Multi-Step Reasoning:** The Gemini 2.5 Flash agent evaluates the prompt and determines which tools to invoke.
3. **Tool Execution:**
   * `retrieve_contract_clauses`: Connects to Snowflake (securely bypassing MFA via session state) to search the `CONTRACT_CHUNKS` table for relevant text.
   * `calculate_risk_level`: Evaluates the retrieved legal text for high-risk language (e.g., penalties, breach, indemnification).
4. **Final Synthesis:** The agent loops the retrieved data through its reasoning engine and outputs a grounded, highly accurate compliance verdict to the user.

## ⚙️ Setup & Installation

### 1. Prerequisites
* Python 3.10+
* A Snowflake account with the `LEXGUARD_DB` database and `CONTRACT_CHUNKS` table populated.
* A Google Gemini API Key.

### 2. Environment Variables
Create a `.env` file in the root directory and add the following credentials:
```env
GEMINI_API_KEY=your_gemini_api_key_here

SNOW_ACCOUNT=your_snowflake_account_locator
SNOW_USER=your_snowflake_username
SNOW_PASS=your_snowflake_password
SNOW_ROLE=TRAINING_ROLE
SNOW_WH=COMPUTE_WH
SNOW_DB=LEXGUARD_DB
SNOW_SCHEMA=CONTRACT_DATA
