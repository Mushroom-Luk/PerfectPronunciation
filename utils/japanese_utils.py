import jaconv
import re


def hiragana_to_romaji(text):
    """Convert Hiragana to Romaji."""
    try:
        return jaconv.hiragana2alphabet(text)
    except:
        return text


def katakana_to_romaji(text):
    """Convert Katakana to Romaji."""
    try:
        return jaconv.katakana2alphabet(text)
    except:
        return text


def japanese_to_romaji(text):
    """Convert Japanese text to Romaji."""
    try:
        # Convert hiragana and katakana to romaji
        romaji_text = jaconv.jaconv.kana2alphabet(text)
        return romaji_text
    except:
        return text


def get_japanese_sample_texts():
    """Get sample Japanese texts for practice."""
    return {
        "Beginner": [
            "こんにちは",
            "おはよう",
            "ありがとう",
            "すみません",
            "はじめまして"
        ],
        "Intermediate": [
            "おはようございます",
            "ありがとうございます",
            "すみませんでした",
            "よろしくお願いします",
            "お疲れ様でした"
        ],
        "Advanced": [
            "日本語を勉強しています",
            "今日は良い天気ですね",
            "どうぞよろしくお願いいたします",
            "申し訳ございませんでした",
            "お忙しい中ありがとうございます"
        ]
    }


def analyze_japanese_text(text):
    """Analyze Japanese text composition."""
    hiragana_count = len(re.findall(r'[ひらがな]', text))
    katakana_count = len(re.findall(r'[カタカナ]', text))
    kanji_count = len(re.findall(r'[一-龯]', text))

    return {
        'total_characters': len(text),
        'hiragana_count': hiragana_count,
        'katakana_count': katakana_count,
        'kanji_count': kanji_count
    }


def get_pronunciation_tips():
    """Get general pronunciation tips for Japanese."""
    return [
        "🎯 **Syllable Timing**: Japanese has even syllable timing - each mora takes the same amount of time",
        "🔊 **Pitch Accent**: Pay attention to high and low pitch patterns in words",
        "📝 **Clear Articulation**: Pronounce each syllable clearly and distinctly",
        "⏱️ **Rhythm**: Maintain steady rhythm throughout your speech",
        "🎵 **Intonation**: Japanese has relatively flat intonation compared to English",
        "🗣️ **Vowel Sounds**: Japanese has 5 pure vowel sounds - keep them consistent",
        "🔤 **Consonants**: Most consonants are softer than English equivalents"
    ]