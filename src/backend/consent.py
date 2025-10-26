# consent_prompt.py

def ask_for_consent() -> bool:
    """
    Display the consent form in the terminal and prompt for yes/no.
    Returns:
        True  -> user consented, the program that called ask_for_consent will direct it to the file parsing page
        False -> user did not consent. The user will not be allowed to upload files.
    """
    consent_text = """=====================================================================
            PROJECT CONSENT FORM: MINING DIGITAL WORK ARTIFACTS
=====================================================================

1. PURPOSE OF THE APPLICATION
---------------------------------------------------------------------
This application analyzes a zipped project folder that you provide
in order to generate summaries, metrics, and résumé-ready highlights.

All analysis is performed locally on your device using the Llama Stack,
a privacy-preserving AI framework. No data is transmitted to any
external server or third-party API.


2. SCOPE OF DATA ACCESS
---------------------------------------------------------------------
When you upload a ZIP file, the app will only access the contents
within that ZIP. It will not scan or access any other files or
directories on your device.

The application may extract and process the following:
  - File metadata (names, sizes, timestamps, types)
  - Readable text (e.g., README files, notes, documentation, comments)
  - Programming code (for classification and metrics)
  - Image metadata (for creative project context)


3. LOCAL ANALYSIS (LLAMA STACK)
---------------------------------------------------------------------
All data analysis occurs locally using the Llama Stack, which runs
entirely on your device.

Features of Local Processing:
  - No internet connection is required for analysis.
  - All computations and model inferences are performed locally using
    Llama models (via Ollama or vLLM).
  - The model and its runtime environment are sandboxed to prevent
    unauthorized data access.
  - Summaries and metrics are generated using local templates and
    natural language generation tools.

Privacy Considerations:
  - Your data never leaves your device.
  - No external APIs or cloud-based services are contacted.
  - The model and system logs remain local and are not shared or synced.


4. DATA STORAGE
---------------------------------------------------------------------
Stored locally on your device:
  - SQLite database containing project metadata, metrics, summaries,
    and your consent record.
  - Extracted text snippets used for local analysis only.
  - Timestamped consent log.

You may disable local logging of prompts/responses at any time in:
  Settings → Privacy


5. DATA DELETION
---------------------------------------------------------------------
You may delete all stored data through:
  Settings → Privacy → Delete All Data

This action removes:
  - All local databases, caches, summaries, and consent records.
  - Any temporary extracted files or logs generated during processing.

Since no external data transmission occurs, deletion is immediate and
complete.


6. VOLUNTARY PARTICIPATION
---------------------------------------------------------------------
Your participation and data submission are voluntary. You may withdraw
consent at any time through:
  Settings → Consent

After withdrawal, the application will cease all data analysis and
delete existing data if requested.


7. RELATED PRIVACY POLICIES
---------------------------------------------------------------------
  - Llama Stack (Meta): https://ai.meta.com/llama/
  - Ollama Runtime:     https://ollama.ai/privacy


8. CONSENT DECISION
---------------------------------------------------------------------
Please confirm the following:

      I consent to the app analyzing my uploaded ZIP locally using the
      Llama Stack. I understand that no data will be transmitted
      externally, and all processing occurs on my device for maximum
      privacy.

=====================================================================

"""
    print(consent_text)

    while True:
        try:
            resp = input("Do you consent to the terms above? [y/n]: ").strip().lower()
        except EOFError:
            # If input stream is closed (e.g., piped), default to no consent
            return False

        if resp in ("y", "yes"):
            return True
        if resp in ("n", "no"):
            return False
        print("Please type 'y' or 'n' and press Enter.")


# allow running this module directly for quick manual testing.
if __name__ == "__main__":
    consent = ask_for_consent()
    print(f"\nConsent granted: {consent}")
