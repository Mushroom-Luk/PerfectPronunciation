import jaconv
import pykakasi
import re


def get_sample_texts():
    return {
        "Japanese": {
            "Beginner": ["こんにちは", "ありがとう", "すみません"],
            "Intermediate": ["おはようございます", "よろしくお願いします"],
            "Advanced": ["日本語を勉強しています", "今日は良い天気ですね"]
        },
        "English": {
            "Beginner": ["Hello", "Thank you", "Good morning"],
            "Intermediate": ["How are you today?", "Nice to meet you"],
            "Advanced": ["I am learning English pronunciation", "The weather is beautiful today"]
        },
        "Mandarin": {
            "Beginner": ["你好", "谢谢", "对不起"],
            "Intermediate": ["你好吗？", "很高兴见到你"],
            "Advanced": ["我在学习中文发音", "今天天气很好"]
        },
        "Cantonese": {
            "Beginner": ["你好", "多謝", "唔好意思"],
            "Intermediate": ["你好嗎？", "好高興見到你"],
            "Advanced": ["我喺度學粵語發音", "今日天氣好好"]
        },
        "German": {
            "Beginner": ["Hallo", "Danke", "Entschuldigung"],
            "Intermediate": ["Wie geht es dir?", "Freut mich dich kennenzulernen"],
            "Advanced": ["Ich lerne deutsche Aussprache", "Das Wetter ist heute schön"]
        },
        "French": {
            "Beginner": ["Bonjour", "Merci", "Au revoir"],
            "Intermediate": ["Comment ça va ?", "Je m'appelle..."],
            "Advanced": ["J'apprends la prononciation française", "Il fait beau aujourd'hui"]
        }
    }


def get_translation_placeholder_text(display_lang, speak_lang):
    """Generates dynamic placeholder text for the translation mode text area."""
    # Dictionary of language names localized to each display language
    lang_names = {
        "English": {
            "English": "English",
            "Japanese": "Japanese",
            "Mandarin": "Mandarin",
            "Cantonese": "Cantonese",
            "German": "German",
            "French": "French"
        },
        "Japanese": {
            "English": "英語",
            "Japanese": "日本語",
            "Mandarin": "中国語",
            "Cantonese": "広東語",
            "German": "ドイツ語",
            "French": "フランス語"
        },
        "Mandarin": {
            "English": "英语",
            "Japanese": "日语",
            "Mandarin": "中文",
            "Cantonese": "粤语",
            "German": "德语",
            "French": "法语"
        },
        "Cantonese": {
            "English": "英文",
            "Japanese": "日文",
            "Mandarin": "普通话",
            "Cantonese": "廣東話",
            "German": "德文",
            "French": "法文"
        },
        "German": {
            "English": "Englisch",
            "Japanese": "Japanisch",
            "Mandarin": "Mandarin",
            "Cantonese": "Kantonesisch",
            "German": "Deutsch",
            "French": "Französisch"
        },
        "French": {
            "English": "anglais",
            "Japanese": "japonais",
            "Mandarin": "mandarin",
            "Cantonese": "cantonais",
            "German": "allemand",
            "French": "français"
        }
    }

    # Get localized names
    local_names = lang_names.get(display_lang, lang_names["English"])
    display_local = local_names.get(display_lang, display_lang)
    speak_local = local_names.get(speak_lang, speak_lang)

    # Templates with placeholders for localized names
    templates = {
        "English": """Paste your bilingual text here. The AI will parse it based on the languages you selected.

For example, if you paste:
---
This is the first sentence in {display_local}.

{speak_local} Translation
This is the first sentence in {speak_local}.
---
The app will create a practice chunk where you read the {display_local} text and speak the {speak_local} translation.""",
        "Japanese": """ここに多言語テキストを貼り付けてください。選択した言語に基づいてAIが解析します。

例えば、以下のように貼り付けます：
---
これは{display_local}の最初の文です。

{speak_local}の翻訳
これは{speak_local}の最初の文です。
---
アプリは、{display_local}のテキストを読んで{speak_local}の翻訳を話す練習チャンクを作成します。""",
        "Mandarin": """请在此处粘贴您的双语文本。AI将根据您选择的语言进行解析。

例如，如果您粘贴：
---
这是第一个{display_local}句子。

{speak_local}翻译
这是第一个{speak_local}句子。
---
该应用程序将创建一个练习块，您可以在其中阅读{display_local}文本并说出{speak_local}的翻译。""",
        "Cantonese": """請喺呢度貼上你嘅雙語文本。AI會根據你選擇嘅語言進行解析。

例如，如果你貼上：
---
呢個係第一句{display_local}。

{speak_local}翻譯
呢個係第一句{speak_local}。
---
個App會創建一個練習塊，你可以喺嗰度讀{display_local}文本，然後講出{speak_local}嘅翻譯。""",
        "German": """Fügen Sie hier Ihren zweisprachigen Text ein. Die KI wird ihn basierend auf den von Ihnen ausgewählten Sprachen analysieren.

Zum Beispiel, wenn Sie einfügen:
---
Dies ist der erste Satz auf {display_local}.

{speak_local}-Übersetzung
Dies ist der erste Satz auf {speak_local}.
---
Die App erstellt einen Übungsblock, in dem Sie den {display_local} Text lesen und die {speak_local}-Übersetzung sprechen.""",
        "French": """Collez votre texte bilingue ici. L'IA l'analysera en fonction des langues que vous avez sélectionnées.

Par exemple, si vous collez :
---
Ceci est la première phrase en {display_local}.

Traduction en {speak_local}
Ceci est la première phrase en {speak_local}.
---
L'application créera un bloc d'exercice où vous lirez le texte en {display_local} et prononcerez la traduction en {speak_local}."""
    }

    # Get the template and format it
    template = templates.get(display_lang, templates["English"])
    return template.format(display_local=display_local, speak_local=speak_local)


def split_text_into_sentences(text):
    """Splits text into sentences using regex, handling various punctuation and newlines."""
    if not text:
        return []
    # Split by sentence-ending punctuation (.?!。？！) or newlines, keeping the delimiter in the output.
    parts = re.split(r'([.?!。？！\n])', text)
    sentences = []
    current_sentence = ""
    for part in parts:
        if part:  # Ignore empty strings that can result from re.split
            current_sentence += part
            # If the part is a delimiter, the sentence is complete.
            if part in ".?!。？！\n":
                stripped_sentence = current_sentence.strip()
                if stripped_sentence:
                    sentences.append(stripped_sentence)
                current_sentence = ""
    # Add any remaining text that didn't end with a delimiter
    if current_sentence.strip():
        sentences.append(current_sentence.strip())

    return [s for s in sentences if s]


def get_romanization_with_words(text, language):
    """Get word-by-word romanization for hover display"""
    if language == "Japanese":
        try:
            kks = pykakasi.kakasi()
            result = kks.convert(text)
            return [(item['orig'], item['hepburn']) for item in result]
        except:
            return [(char, jaconv.kana2alphabet(char)) for char in text]
    return [(text, text)]


def fill_japanese_phonemes(word):
    """Fill empty Japanese phonemes using pykakasi"""
    try:
        kks = pykakasi.kakasi()
        result = kks.convert(word)
        if result:
            romaji = result[0]['hira']
            return list(romaji)
    except:
        pass
    return []


def get_pronunciation_tips(language):
    tips = {
        "Japanese": [
            "🎯 Even syllable timing - each mora takes the same time",
            "🔊 Pay attention to pitch accent patterns",
            "📝 Pronounce each syllable clearly"
        ],
        "English": [
            "🎯 Focus on stress patterns in words",
            "🔊 Practice vowel sounds clearly",
            "📝 Work on consonant clusters"
        ],
        "Mandarin": [
            "🎯 Master the four tones",
            "🔊 Practice retroflex sounds",
            "📝 Clear distinction between similar sounds"
        ],
        "Cantonese": [
            "🎯 Practice the six tones",
            "🔊 Work on final consonants",
            "📝 Focus on clear articulation"
        ],
        "German": [
            "🎯 Practice umlauts (ä, ö, ü)",
            "🔊 Work on consonant combinations",
            "📝 Focus on word stress patterns"
        ],
        "French": [
            "🎯 Master nasal vowels (e.g., 'on', 'en', 'in', 'un')",
            "🔊 Practice the 'r' sound (uvular fricative)",
            "📝 Pay attention to 'liaison' (linking words together)"
        ]
    }
    return tips.get(language, [])