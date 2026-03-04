# Individual Contribution Report
**Name:** Manan Koradiya
**Role:** Agent Architect

**Personal Responsibilities & Implemented Components:**
* Engineered the `tools.py` file, wrapping Snowflake SQL queries and Python risk-assessment logic into LLM-callable functions.
* Implemented the dynamic Multi-Factor Authentication (MFA) passthrough from the Streamlit UI to the Snowflake connector.
* Designed the multi-step execution loop in `agent.py` using the `google-genai` SDK.

**Links to Commits:**
* (https://github.com/Manan151179/BIG_DATA_LAB6/commit/7c4ea6ef3a560c1832bbd5e177517ba253e99394#diff-2171db0cf84575462627421658645f2d76c71fb0e13dceb297c41e443bfd8af7)

**Technical Reflection:**
Integrating the new Gemini SDK natively without relying on an external framework like LangChain taught me the mechanics of manual tool dispatching. The biggest technical hurdle was managing the Snowflake MFA requirement within a continuous agent loop. I overcame this by capturing the TOTP code in the Streamlit session state and passing it directly into the tool functions, allowing the agent to authenticate dynamically without crashing.
