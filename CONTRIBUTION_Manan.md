# Individual Contribution Report
**Name:** Manan Koradiya
**Role:** Agent Architect & System Integrator

---

## Personal Responsibilities & Implemented Components

### 1. Agentic Reasoning Engine (`agent.py`)
- Designed and implemented the **multi-step reasoning loop** using the `google-genai` SDK (Gemini 2.5 Flash), enabling the agent to iteratively select tools, execute them, and synthesize compliance verdicts.
- Authored the **system prompt** defining LexGuard's "Recall-Then-Reason" pipeline: the agent first retrieves contract clauses from Snowflake, then evaluates risk, and finally produces a grounded compliance verdict.
- Implemented the **tool dispatch mechanism** (`AVAILABLE_TOOLS` dictionary) that maps string function names returned by the LLM to actual Python callables, handling both `retrieve_contract_clauses` and `calculate_risk_level`.
- Added a **max-steps guard** (`max_steps = 5`) to prevent infinite tool-calling loops, with graceful timeout messaging.
- Configured the model with `temperature=0.1` to ensure analytical, low-variance responses suitable for legal compliance tasks.

### 2. LLM-Callable Tool Functions (`tools.py`)
- Wrapped Snowflake SQL queries into the `retrieve_contract_clauses()` function, which performs `ILIKE` keyword search against the `CONTRACT_CHUNKS` table and returns formatted evidence strings.
- Implemented `calculate_risk_level()` — a deterministic, rule-based risk classifier that flags clauses containing "indemnify" or "immediate termination" as **High Risk**, "penalty" or "breach" as **Medium Risk**, and all others as **Low Risk**.
- Added `retrieve_local_clauses()` as an offline alternative to the Snowflake retrieval tool, backed by the `LocalStore` inverted keyword index for testing without cloud credentials.

### 3. Streamlit Chat Interface (`app.py`)
- Built the interactive **Streamlit chat UI** with persistent conversation history (`st.session_state.messages`), enabling multi-turn compliance audit dialogues.
- Engineered the **MFA passthrough mechanism**: the sidebar captures the user's 6-digit TOTP code, stores it in `os.environ["SNOW_MFA"]`, and the `tools.py` functions read it at connection time — solving the problem of Snowflake MFA within a continuously running Streamlit app.
- Added input validation to block agent execution if the MFA code is missing, displaying a clear error prompt to the user.

### 4. System Integration
- Connected all pipeline stages end-to-end: PDF ingestion → Snowflake storage → agent retrieval → risk analysis → Streamlit presentation.
- Ensured `config.py` is imported at the top of every module to guarantee deterministic seeding across all components.

---

## Links to Commits
- [Initial commit for Lab 6: LexGuard Agent](https://github.com/Manan151179/BIG_DATA_LAB6/commit/7c4ea6e)
- [Organize artifacts and update smoke tests](https://github.com/Manan151179/BIG_DATA_LAB6/commit/098a9d0)

---

## Technical Reflection

Integrating the new Gemini SDK natively without relying on an external framework like LangChain taught me the mechanics of manual tool dispatching — parsing `response.function_calls`, executing the corresponding Python function, and packaging the result back as a `types.Part.from_function_response()` for the next iteration. The biggest technical hurdle was managing the Snowflake MFA requirement within a continuous agent loop. Since TOTP codes rotate every 30 seconds and the Streamlit app runs as a long-lived process, I solved this by capturing the TOTP code in the Streamlit session state sidebar and injecting it into the environment variables, allowing the agent to authenticate dynamically without crashing mid-conversation. This approach eliminated the need for `externalbrowser` authentication, which was unreliable in headless/server deployments.
