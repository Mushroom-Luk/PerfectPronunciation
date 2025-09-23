import jaconv
import cutlet
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
        }
    }

def get_romanization_with_words(text, language):
    """Get word-by-word romanization for hover display"""
    if language == "Japanese":
        try:
            kks = pykakasi.kakasi()
            result = kks.convert(text)
            return [(item['orig'], item['hepburn']) for item in result]
        except:
            # Fallback to simple conversion
            return [(char, jaconv.kana2alphabet(char)) for char in text]
    return [(text, text)]

def fill_japanese_phonemes(word):
    """Fill empty Japanese phonemes using pykakasi"""
    try:
        kks = pykakasi.kakasi()
        result = kks.convert(word)
        if result:
            # Convert to phoneme-like representation
            romaji = result[0]['hepburn']
            return list(romaji)  # Simple character split as phonemes
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
        ]
    }
    return tips.get(language, [])