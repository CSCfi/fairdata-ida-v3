# This is a temporary one-off script to merge translations from JS and JSON files into a single JSON file, as
# now used in the new translation management methodology in the IDA app from the unified translation.json file.
# It will be discarded once the update is complete.

import os
import json
import re

def load_js_translations(js_file):
    print(f"Loading JS translations from: {js_file}")
    translations = {}
    with open(js_file, 'r', encoding='utf-8') as f:
        content = f.read()
        
        pattern = re.compile(r'[^\{]*(\{.*\}).*', re.DOTALL)

        match = pattern.search(content)
        
        if match:
            try:
                # Parse the JSON-like content from the JS file
                js_translations = json.loads(match.group(1))
                print(f"Found {len(js_translations)} translations in JS file: {js_file}")
                
                # Add the translations to the dictionary
                for key, value in js_translations.items():
                    translations[key] = value
            except json.JSONDecodeError as e:
                print(f"Error decoding JSON in JS file: {js_file} - {e}")
        else:
            print(f"No translation block found in JS file: {js_file}")
    
    return translations

def load_json_translations(json_file):
    print(f"Loading JSON translations from: {json_file}")
    with open(json_file, 'r', encoding='utf-8') as f:
        json_translations = json.load(f)
        translations = json_translations['translations']
        print(f"Found {len(translations)} translations in JSON file: {json_file}")
        return translations

def merge_translations(all_translations, js_translations, json_translations, lang_code):
    
    # Add translations from js file
    for key, value in js_translations.items():
        if key not in all_translations:
            all_translations[key] = {}
        all_translations[key][lang_code] = value
    
    # Add translations from json file
    for key, value in json_translations.items():
        if key not in all_translations:
            all_translations[key] = {}
        all_translations[key][lang_code] = value

def build_translations(language_codes):
    all_translations = {}

    # Loop through language codes (fi, sv, etc.)
    for lang_code in language_codes:
        js_file = f'{lang_code}.js'
        json_file = f'{lang_code}.json'

        js_translations = load_js_translations(js_file) if os.path.exists(js_file) else {}
        json_translations = load_json_translations(json_file) if os.path.exists(json_file) else {}

        # Merge translations from both JS and JSON files
        merge_translations(all_translations, js_translations, json_translations, lang_code)

    return all_translations

def main():
    language_codes = ['fi', 'sv']  # Define the language codes you need to load
    translations = build_translations(language_codes)

    print(f"Total translations: {len(translations)}")

    # Sort the translations dictionary by key
    sorted_translations = {key: translations[key] for key in sorted(translations)}

    # Output the result as a translations.json
    with open('translations.json', 'w', encoding='utf-8') as f:
        f.write(json.dumps(sorted_translations, indent=4, ensure_ascii=False))

if __name__ == "__main__":
    main()

