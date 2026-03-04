import os
import streamlit as st
import snowflake.connector

# Removed externalbrowser to use standard password auth that worked for ingest.py

@st.cache_resource
def get_snowflake_connection():
    print("❄️ Opening persistent Snowflake connection...")
    
    # Check for MFA in environment, but if it's missing, ask in the terminal!
    mfa_code = os.getenv("SNOW_MFA")
    if not mfa_code:
        mfa_code = input("\n🔐 Enter your current Snowflake MFA/TOTP code (6 digits): ").strip()

    return snowflake.connector.connect(
        user=os.getenv("SNOW_USER"),
        password=os.getenv("SNOW_PASS"),
        account=os.getenv("SNOW_ACCOUNT"),
        role=os.getenv("SNOW_ROLE", "TRAINING_ROLE"),
        warehouse=os.getenv("SNOW_WH", "COMPUTE_WH"),
        database=os.getenv("SNOW_DB", "LEXGUARD_DB"),
        schema=os.getenv("SNOW_SCHEMA", "CONTRACT_DATA"),
        passcode=mfa_code  # Uses the fresh code you just typed
    )

def retrieve_contract_clauses(search_term: str) -> str:
    """
    Searches the Snowflake database for specific legal contract clauses based on a keyword.
    Use this tool whenever the user asks about the contents of the contracts.

    Args:
        search_term: A specific keyword or short phrase to search for (e.g., "termination", "liability").

    Returns:
        A string containing the retrieved contract chunks, or an error message if the search fails.
    """
    print(f"🔧 Tool Invoked: Searching Snowflake for '{search_term}'...")
    
    try:
        conn = get_snowflake_connection()
        cursor = conn.cursor()
        
        query = f"""
            SELECT DOC_NAME, CHUNK_TEXT 
            FROM CONTRACT_CHUNKS 
            WHERE CHUNK_TEXT ILIKE '%{search_term}%'
            LIMIT 5;
        """
        cursor.execute(query)
        results = cursor.fetchall()
        
        if not results:
            return f"No evidence found in the contracts for '{search_term}'."
            
        evidence = []
        for row in results:
            evidence.append(f"[Source: {row[0]}]\n{row[1]}")
            
        return "\n\n---\n\n".join(evidence)
        
    except Exception as e:
        # Added this so we can see the exact raw error in your Mac terminal
        print(f"\n❌ RAW SNOWFLAKE ERROR: {str(e)}\n") 
        return f"Database error: {str(e)}"

def calculate_risk_level(clause_text: str) -> str:
    """
    Analyzes a specific contract clause to determine if it contains high-risk language.
    Use this tool if the user asks to evaluate risk or danger in a clause.

    Args:
        clause_text: The exact text of the legal clause to evaluate.

    Returns:
        A string indicating 'High Risk', 'Medium Risk', or 'Low Risk' with a brief reason.
    """
    print("🔧 Tool Invoked: Calculating risk level...")
    
    text_lower = clause_text.lower()
    if "indemnify" in text_lower or "immediate termination" in text_lower:
        return "High Risk: Contains indemnification or immediate termination clauses."
    elif "penalty" in text_lower or "breach" in text_lower:
        return "Medium Risk: Mentions penalties or breach conditions."
    else:
        return "Low Risk: No standard high-risk keywords detected."