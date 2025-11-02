# translate_epg.py (v8 - Polish GZIP Edition)
import requests
import xml.etree.ElementTree as ET
import time
from googletrans import Translator
import gzip # <-- 1. ΠΡΟΣΘΗΚΗ: Εισάγουμε τη βιβλιοθήκη για GZIP

# --- Οριστική λίστα με τα Channel IDs που μας ενδιαφέρουν ---
TARGET_CHANNELS = {
    "Sportklub HD.pl",
    "Sportklub.HD.pl"
}
# ----------------------------------------------------------------

# ΑΛΛΑΓΗ: Βάζουμε το νέο URL που τελειώνει σε .gz
SOURCE_URL = "https://epgshare01.online/epgshare01/epg_ripper_PL1.xml.gz"
OUTPUT_FILE = "epg-en.xml"

# --- Caching & Translator Initialization ---
translation_cache = {}
api_calls_made = 0
translator = Translator()

# --- Functions (η συνάρτηση μετάφρασης παραμένει η ίδια) ---
def translate_text(text, target_lang='en', source_lang='pl'):
    global api_calls_made
    if not text or not text.strip(): return text
    if text in translation_cache: return translation_cache[text]

    for attempt in range(3):
        try:
            translated_result = translator.translate(text, dest=target_lang, src=source_lang)
            translated_text = translated_result.text
            api_calls_made += 1
            print(f"API Call #{api_calls_made}: Translated '{text[:30]}...' to '{translated_text[:30]}...'")
            translation_cache[text] = translated_text
            time.sleep(1)
            return translated_text
        except Exception as e:
            print(f"Attempt {attempt + 1}/3 failed for text '{text[:30]}...'. Error: {e}")
            time.sleep(2)
    print(f"Warning: All translation attempts failed for text: '{text[:30]}...'. Returning original text.")
    return text

# --- Main Logic (με τη λογική του φιλτραρίσματος) ---
def main():
    print(f"Downloading EPG from {SOURCE_URL}...")
    try:
        response = requests.get(SOURCE_URL)
        response.raise_for_status()
        
        # --- 2. ΠΡΟΣΘΗΚΗ: Αποσυμπιέζουμε το περιεχόμενο .gz ---
        xml_content = gzip.decompress(response.content)
        # ---------------------------------------------------

    except requests.exceptions.RequestException as e:
        print(f"Failed to download EPG file: {e}")
        return
    except gzip.BadGzipFile:
        print("Error: The downloaded file is not a valid GZIP file.")
        return

    print("Parsing original XML content...")
    parser = ET.XMLParser(encoding="utf-8")
    original_root = ET.fromstring(xml_content, parser=parser)

    new_root = ET.Element('tv')

    print(f"Filtering for target channels...")
    for channel in original_root.findall('channel'):
        if channel.get('id') in TARGET_CHANNELS:
            print(f"Found and added target channel: {channel.get('id')}")
            new_root.append(channel)

    print("Filtering and translating programmes...")
    processed_count = 0
    for prog in original_root.findall('programme'):
        channel_id = prog.get('channel')
        if channel_id in TARGET_CHANNELS:
            processed_count += 1
            
            title_element = prog.find('title')
            if title_element is not None and title_element.text:
                title_element.text = translate_text(title_element.text)
            
            desc_element = prog.find('desc')
            if desc_element is not None and desc_element.text:
                desc_element.text = translate_text(desc_element.text)
            
            new_root.append(prog)

    print("\n--- Translation Summary ---")
    print(f"Total programmes found and processed: {processed_count}")
    print(f"Total unique phrases translated (API calls): {api_calls_made}")
    print("--------------------------\n")

    print(f"Saving filtered and translated EPG to {OUTPUT_FILE}...")
    new_tree = ET.ElementTree(new_root)
    new_tree.write(OUTPUT_FILE, encoding='UTF-8', xml_declaration=True)
    print("Job complete!")

if __name__ == "__main__":
    main()
