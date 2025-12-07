#!/usr/bin/env python3
"""
Quick verification script to test the consent flow.
This demonstrates both local consent and external service consent.
"""

from src.backend.consent import ask_for_consent, ask_for_external_service_consent

def main():
    print("="*70)
    print("CONSENT SYSTEM VERIFICATION")
    print("="*70)
    print()
    print("This script tests the updated consent system with:")
    print("  1. Local analysis consent (default)")
    print("  2. External service consent (Google Gemini)")
    print()
    print("="*70)
    print()
    
    # Test basic consent
    print("STEP 1: Testing basic (local) consent")
    print("-"*70)
    basic_consent = ask_for_consent()
    print()
    print(f"Result: Basic consent = {basic_consent}")
    print()
    
    if not basic_consent:
        print("⚠️  User declined basic consent. Exiting.")
        return
    
    # Test external service consent
    print()
    print("="*70)
    print("STEP 2: Testing external service (Gemini) consent")
    print("-"*70)
    external_consent = ask_for_external_service_consent("Google Gemini API")
    print()
    print(f"Result: External service consent = {external_consent}")
    print()
    
    # Summary
    print()
    print("="*70)
    print("VERIFICATION SUMMARY")
    print("="*70)
    print(f"✓ Basic (local) consent:      {basic_consent}")
    print(f"✓ External service consent:   {external_consent}")
    print()
    
    if basic_consent and external_consent:
        print("✅ FULL CONSENT GRANTED")
        print("   → User can use both local and AI-enhanced analysis")
    elif basic_consent and not external_consent:
        print("✅ LOCAL CONSENT ONLY")
        print("   → User can use local analysis")
        print("   → AI-enhanced analysis (Gemini) declined")
    else:
        print("❌ NO CONSENT")
        print("   → User cannot use the application")
    
    print()
    print("="*70)

if __name__ == "__main__":
    main()
