# Individual Contribution Report
**Name:** [Your Name]
**Role:** [e.g., Lead Agent Architect / Database Engineer]

**Personal Responsibilities & Implemented Components:**
* Engineered the `tools.py` file, wrapping Snowflake SQL queries and Python risk-assessment logic into LLM-callable functions.
* Implemented the dynamic Multi-Factor Authentication (MFA) passthrough from the Streamlit UI to the Snowflake connector.
* Designed the multi-step execution loop in `agent.py` using the `google-genai` SDK.

**Links to Commits:**
* [Link to commit where you added tools.py]
* [Link to commit where you updated the Streamlit UI]

**Technical Reflection:**
Integrating the new Gemini SDK natively without relying on an external framework like LangChain taught me the mechanics of manual tool dispatching. The biggest technical hurdle was managing the Snowflake MFA requirement within a continuous agent loop. I overcame this by capturing the TOTP code in the Streamlit session state and passing it directly into the tool functions, allowing the agent to authenticate dynamically without crashing.