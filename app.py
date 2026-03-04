import streamlit as st
import os

# Import our working agent loop
from agent import run_lexguard_agent

# 1. Page Configuration
st.set_page_config(page_title="LexGuard Auditor", page_icon="⚖️", layout="centered")
st.title("⚖️ LexGuard Compliance Auditor")
st.markdown("A Neuro-Symbolic Agent for auditing Residential Lease Agreements.")

# 2. Sidebar Configuration (The MFA Fix)
with st.sidebar:
    st.header("⚙️ Database Authentication")
    st.write("Snowflake requires a live MFA code to fetch contract clauses.")
    
    mfa_code = st.text_input("Enter 6-digit TOTP Code:", type="password", max_chars=6)
    
    if mfa_code:
        # Save the code temporarily in the environment so tools.py can grab it
        os.environ["SNOW_MFA"] = mfa_code
        st.success("MFA code cached for this session.")
    else:
        st.warning("⚠️ Please enter your MFA code before chatting.")

# 3. Initialize Conversation History (Rubric Requirement)
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Hello! I am LexGuard. What contract clauses would you like me to audit today?"}
    ]

# 4. Display Chat History (Rubric Requirement)
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# 5. User Chat Input (Rubric Requirement)
if prompt := st.chat_input("e.g., Are there any high-risk indemnification clauses?"):
    
    # Immediately display the user's question
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Block the request if the user forgot their MFA code
    if not os.getenv("SNOW_MFA"):
        error_msg = "I need your Snowflake MFA code in the sidebar to read the contracts!"
        with st.chat_message("assistant"):
            st.error(error_msg)
        st.session_state.messages.append({"role": "assistant", "content": error_msg})
        st.stop()

    # 6. Loading Indicator & Agent Execution (Rubric Requirement)
    with st.chat_message("assistant"):
        with st.spinner("🧠 LexGuard is recalling clauses and reasoning..."):
            # Call the agent engine we built!
            final_response = run_lexguard_agent(prompt)
            
        # Display the final verdict
        st.markdown(final_response)
        
    # Save the agent's response to history
    st.session_state.messages.append({"role": "assistant", "content": final_response})