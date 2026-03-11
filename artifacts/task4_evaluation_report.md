# Task 4: Agent Evaluation Report

### 1. Simple Scenario (Single Tool / Empty State)
* **User Query:** "Audit the lease agreements to see if the pet deposit amount is compliant."
* **Tools Used:** `retrieve_contract_clauses` (called 3 times iteratively).
* **Number of Reasoning Steps:** 3
* **Accuracy Assessment:** High. The documents did not contain pet clauses.
* **Latency:** ~4 seconds.
* **Analysis:** The agent searched for "pet deposit", found 0 results, reasoned it should try synonyms ("pet policy", "animal"), and gracefully informed the user the data was missing instead of hallucinating.

### 2. Medium Scenario (Error Handling)
* **User Query:** "Find clauses about termination." *(Run without entering MFA code in the sidebar)*
* **Tools Used:** None (blocked at UI level) / `retrieve_contract_clauses` (if bypassed).
* **Number of Reasoning Steps:** 1
* **Accuracy Assessment:** Perfect error handling.
* **Latency:** ~1 second.
* **Analysis:** The system successfully trapped the missing Snowflake MFA code, preventing a catastrophic application crash, and provided a clear system instruction to the user to authenticate.

### 3. Complex Scenario (Reasoning and Synthesis)
* **User Query:** "Search the lease agreements for any clauses mentioning 'indemnify' or 'indemnification', and then calculate the risk level of what you find."
* **Tools Used:** `retrieve_contract_clauses`, `calculate_risk_level`.
* **Number of Reasoning Steps:** 4+ (Retrieval followed by multiple risk calculations).
* **Accuracy Assessment:** High. 
* **Latency:** ~8 seconds.
* **Analysis:** The agent successfully executed a multi-tool chain. It retrieved raw legal text from six different contract chunks, evaluated the risk level of each chunk individually, and synthesized a final "Fails" compliance verdict explaining its reasoning.