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


def ask_for_external_service_consent(service_name: str = "Google Gemini API") -> bool:
    """
    Display consent form specifically for external service usage (Google Gemini).
    This must be called before sending any data to external APIs.
    
    Args:
        service_name: Name of the external service (default: Google Gemini API)
    
    Returns:
        True  -> user consented to external service usage
        False -> user declined, data should NOT be sent externally
    """
    consent_text = f"""=====================================================================
        ⚠️  EXTERNAL SERVICE CONSENT: {service_name}
=====================================================================

⚠️  IMPORTANT PRIVACY NOTICE
---------------------------------------------------------------------
You are about to use AI-ENHANCED ANALYSIS which sends your project
data to an EXTERNAL CLOUD SERVICE.

This is DIFFERENT from local analysis, which keeps all data on your
device.


1. DATA TRANSMISSION TO EXTERNAL SERVICE
---------------------------------------------------------------------
When you run 'analyze-llm', the following will occur:

  ✓ Your source code files will be uploaded to {service_name}
  ✓ Files are temporarily stored on Google Cloud servers
  ✓ Google's AI models will process your code
  ✓ Results are returned to your device
  ✓ Files are deleted from Google servers after analysis

Data Flow:
  Your Device → Google Cloud → AI Processing → Results → Your Device


2. WHAT DATA IS SENT
---------------------------------------------------------------------
The following from your ZIP file will be uploaded:
  - Source code files (.py, .java, .cpp, .js, etc.)
  - Configuration files (package.json, requirements.txt, etc.)
  - Documentation files (README.md, comments in code)
  - Any text-based files under 2MB

NOT sent:
  - Binary files, images, videos
  - Files in ignored directories (.git, node_modules, venv)
  - Environment files (.env, secrets)
  - Files larger than 2MB


3. PRIVACY IMPLICATIONS
---------------------------------------------------------------------
⚠️  By consenting, you acknowledge:

  • Your code will be transmitted over the internet to Google Cloud
  • Google's privacy policy applies to data while on their servers:
    https://cloud.google.com/terms/cloud-privacy-notice
  • Files are deleted after analysis, but Google may retain logs
    according to their data retention policies
  • This service requires internet connectivity
  • Google may use aggregated/anonymized data to improve their models
    (check their privacy policy for current practices)

⚠️  DO NOT USE THIS FEATURE IF:
  • Your code contains proprietary/confidential information
  • Your employer/organization prohibits cloud processing
  • You are working on classified or sensitive projects
  • You have not obtained necessary permissions to share code


4. ALTERNATIVE: LOCAL ANALYSIS
---------------------------------------------------------------------
You can use the standard 'analyze' command instead:
  Command: mda analyze <project.zip>

This performs comprehensive analysis WITHOUT sending data externally:
  ✓ OOP metrics (Python, Java, C++, C)
  ✓ Complexity analysis
  ✓ Git history and contributor analysis
  ✓ Framework and language detection
  ✓ Project quality scoring

The local analysis provides professional-grade insights without
compromising privacy.


5. CONSENT DECISION
---------------------------------------------------------------------
Please confirm the following:

      I consent to uploading THIS SPECIFIC PROJECT to {service_name}
      for AI-enhanced analysis. I understand that:
        • My code will be transmitted to Google Cloud servers
        • Google's privacy policy applies during processing
        • I have permission to share this code externally
        • I can use local analysis instead to keep data private

=====================================================================

"""
    print(consent_text)

    while True:
        try:
            resp = input(f"Do you consent to uploading to {service_name}? [y/n]: ").strip().lower()
        except EOFError:
            # If input stream is closed, default to no consent for external services
            return False

        if resp in ("y", "yes"):
            print(f"\n✓ Consent granted for {service_name}")
            print("  Proceeding with external analysis...\n")
            return True
        if resp in ("n", "no"):
            print(f"\n✗ Consent declined for {service_name}")
            print("  Tip: Use 'mda analyze <project.zip>' for local analysis instead.\n")
            return False
        print("Please type 'y' or 'n' and press Enter.")


# allow running this module directly for quick manual testing.
if __name__ == "__main__":
    print("Testing basic consent:")
    consent = ask_for_consent()
    print(f"\nBasic consent granted: {consent}")
    
    if consent:
        print("\n" + "="*70)
        print("Testing external service consent:")
        external_consent = ask_for_external_service_consent()
        print(f"\nExternal service consent granted: {external_consent}")
