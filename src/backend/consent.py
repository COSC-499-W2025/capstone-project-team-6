# consent_prompt.py


def ask_for_consent() -> bool:
    """
    Display the consent form in the terminal and prompt for yes/no.
    Returns:
        True  -> user consented, the program that called ask_for_consent will direct it to the file parsing page
        False -> user did not consent. The user will not be allowed to upload files.
    """
    consent_text = consent_text = """=====================================================================
            PROJECT CONSENT FORM: MINING DIGITAL WORK ARTIFACTS
=====================================================================

1. PURPOSE OF THE APPLICATION
---------------------------------------------------------------------
This application analyzes a zipped project folder that you provide
in order to generate summaries, metrics, and résumé-ready highlights.

The application offers TWO types of analysis:
  A) LOCAL ANALYSIS (Default): All processing happens on your device.
  B) AI-ENHANCED ANALYSIS (Optional): Uses Google Gemini API for
     advanced insights. Requires separate consent (see below).


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


3. LOCAL ANALYSIS (DEFAULT MODE)
---------------------------------------------------------------------
The standard 'analyze' command performs all computations locally:

Features of Local Processing:
  - No internet connection required.
  - All analysis (OOP metrics, complexity, git history, etc.) runs
    entirely on your device using Python AST parsers and static
    analysis tools.
  - No data transmission to external servers.

Privacy Considerations:
  - Your data never leaves your device during local analysis.
  - No external APIs or cloud-based services are contacted.
  - All logs and results remain local.


4. DATA STORAGE
---------------------------------------------------------------------
Stored locally on your device:
  - SQLite database containing project metadata, metrics, summaries,
    and your consent record.
  - Extracted text snippets used for analysis only.
  - Timestamped consent log.


5. DATA DELETION
---------------------------------------------------------------------
You may delete stored data at any time using the 'mda' CLI:
  Command: mda [delete/remove data options]

This action removes:
  - All local databases, caches, summaries, and consent records.
  - Any temporary extracted files or logs generated during processing.


6. VOLUNTARY PARTICIPATION
---------------------------------------------------------------------
Your participation and data submission are voluntary. You may withdraw
consent at any time through:
  Command: mda consent --update

After withdrawal, the application will cease all data analysis and
delete existing data if requested.


7. CONSENT DECISION
---------------------------------------------------------------------
Please confirm the following:

      I consent to the app analyzing my uploaded ZIP files locally.
      I understand that this consent covers LOCAL analysis only.
      AI-enhanced analysis (Google Gemini) requires separate consent.

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
