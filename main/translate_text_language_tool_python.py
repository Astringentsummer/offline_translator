import argostranslate.package
import argostranslate.translate
import language_tool_python

# Setup LanguageTool (default is en-US)
tool = language_tool_python.LanguageTool('en-US')  # 可改成 'de-DE' 等

def clean_text_with_languagetool(text, lang_code):
    # 重建 LanguageTool 实例（支持多语言）
    lang_map = {'en': 'en-US', 'de': 'de-DE', 'zh': 'zh-CN'}
    if lang_code not in lang_map:
        return text  # 不支持的语言就跳过清洗

    tool = language_tool_python.LanguageTool(lang_map[lang_code])
    return tool.correct(text)

def translate_text(source_lang_code, target_lang_code, text):
    installed_languages = argostranslate.translate.get_installed_languages()
    from_lang = next((lang for lang in installed_languages if lang.code == source_lang_code), None)
    to_lang = next((lang for lang in installed_languages if lang.code == target_lang_code), None)

    if not from_lang or not to_lang:
        return f"Error: Languages '{source_lang_code}' to '{target_lang_code}' not available."

    translation = from_lang.get_translation(to_lang)
    return translation.translate(text)

def main():
    print("Supported languages:")
    print("en = English")
    print("de = German")
    print("zh = Chinese")

    source_lang = input("Enter source language code (e.g., 'en', 'de', 'zh'): ").strip().lower()
    target_lang = input("Enter target language code (e.g., 'en', 'de', 'zh'): ").strip().lower()

    if source_lang == target_lang:
        print("Source and target languages must be different.")
        return

    text = input("Enter text to translate: ").strip()

    # Run grammar/spelling correction
    cleaned_text = clean_text_with_languagetool(text, source_lang)
    print("\nCleaned Text:")
    print(cleaned_text)

    # Translate
    translated = translate_text(source_lang, target_lang, cleaned_text)
    print("\nTranslated Text:")
    print(translated)

if __name__ == "__main__":
    main()
