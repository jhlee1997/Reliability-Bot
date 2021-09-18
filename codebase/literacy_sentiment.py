import logging
import math
import textstat
import asyncio

logger = logging.getLogger()
if logger.handlers:
    for handler in logger.handlers:
        logger.removeHandler(handler)
logging.basicConfig(level=logging.INFO)

def get_spelling_score(text):
    """
    Takes in text
    Returns dictionary with "spelling"
    """
    from spellchecker import SpellChecker
    # list pre-processing
    word_lst = []
    start = 0
    for i in range(len(text)):
        if not text[i].isalpha():
            word_lst.append(text[start:i])
            start = i+1
    word_lst = list(set(word_lst))
    word_lst.sort()
    while "" in word_lst:
        word_lst.remove("")
    spell = SpellChecker()
    # find those words that may be misspelled
    misspelled = spell.unknown(word_lst)
    # scoring
    score = 1- len(misspelled) / len(word_lst)
    threshold = 0.8
    if score >= threshold:
        score = ((score - threshold) / (1 - threshold) * 0.5) + 0.5
    else:
        score = (score / threshold) * 0.5
    return {"spelling": score}

def text_standard(text):

    def legacy_round(number, points=0):
        p = 10 ** points
        return float(math.floor((number * p) + math.copysign(0.5, number))) / p

    grade = []

    # # Appending Flesch Kincaid Grade
    # lower = legacy_round(textstat.flesch_kincaid_grade(text))
    # upper = math.ceil(textstat.flesch_kincaid_grade(text))
    # grade.append(int(lower))
    # grade.append(int(upper))

    # Appending Flesch Reading Easy
    score = textstat.flesch_reading_ease(text)
    if score < 100 and score >= 90:
        grade.append(5)
    elif score < 90 and score >= 80:
        grade.append(6)
    elif score < 80 and score >= 70:
        grade.append(7)
    elif score < 70 and score >= 60:
        grade.append(8)
        grade.append(9)
    elif score < 60 and score >= 50:
        grade.append(10)
    elif score < 50 and score >= 40:
        grade.append(11)
    elif score < 40 and score >= 30:
        grade.append(12)
    else:
        grade.append(13)

    # # Appending SMOG Index
    # lower = legacy_round(textstat.smog_index(text))
    # upper = math.ceil(textstat.smog_index(text))
    # grade.append(int(lower))
    # grade.append(int(upper))

    # Appending Coleman_Liau_Index
    lower = legacy_round(textstat.coleman_liau_index(text))
    upper = math.ceil(textstat.coleman_liau_index(text))
    grade.append(int(lower))
    grade.append(int(upper))

    # # Appending Automated_Readability_Index
    # lower = legacy_round(textstat.automated_readability_index(text))
    # upper = math.ceil(textstat.automated_readability_index(text))
    # grade.append(int(lower))
    # grade.append(int(upper))

    # Appending Dale_Chall_Readability_Score
    lower = legacy_round(textstat.dale_chall_readability_score(text))
    upper = math.ceil(textstat.dale_chall_readability_score(text))
    grade.append(int(lower))
    grade.append(int(upper))

    # Appending Linsear_Write_Formula
    lower = legacy_round(textstat.linsear_write_formula(text))
    upper = math.ceil(textstat.linsear_write_formula(text))
    grade.append(int(lower))
    grade.append(int(upper))

    # # Appending Gunning Fog Index
    # lower = legacy_round(textstat.gunning_fog(text))
    # upper = math.ceil(textstat.gunning_fog(text))
    # grade.append(int(lower))
    # grade.append(int(upper))

    # Finding the Readability Consensus based upon all the above tests
    # d = Counter(grade)
    # final_grade = d.most_common(1)
    logger.info("Grade list = " + str(grade))

    score = sum(grade) / len(grade)
    return score

def get_reading_score(text):
    """
    Takes in text
    Returns dictionary with "reading"
    """
    # score = textstat.flesch_reading_ease(text)
    # if score < 0:
    #     score = 1.0
    # else:
    #     score = 1.0 - score/121.22
    # age = []
    # age.append(textstat.flesch_kincaid_grade(text))
    # age.append(textstat.gunning_fog(text))
    # age.append(textstat.smog_index(text))
    # age.append(textstat.automated_readability_index(text))
    # age.append(textstat.coleman_liau_index(text))
    # age.append(textstat.linsear_write_formula(text))
    # logger.info("Grade list = " + str(age))
    # age = sum(age)/len(age)
    grade = text_standard(text)
    logger.info("grade output by textstat = " + str(grade))
    score = min(grade / 13, 1)
    # if age >= 14:
    #     score = ((age - 14) / 4 * 0.5) + 0.5
    #     logger.info("age >= 14, age = " + str(age) + "score = " + str(score))
    # else:
    #     score = (age / 14) * 0.5
    #     logger.info("age < 14, age = " + str(age) + "score = " + str(score))
    return {"reading": score}


def get_literacy_score(text):
    """
    Takes in text
    Returns dictionary with "spelling", "reading", and "literacy"
    """
    dic = get_spelling_score(text)
    reading = get_reading_score(text)
    dic.update(reading)
    score = dic["spelling"] * dic["reading"]
    dic["literacy"] = score
    return dic



def get_sentiment_score(text):
    """
    Takes in string of text
    Returns a dictionary of "sentiment"
    """
    import boto3
    comprehend = boto3.client("comprehend")
    response = comprehend.detect_sentiment(Text=text, LanguageCode = "en")
    pos = response["SentimentScore"]["Positive"]
    neg = response["SentimentScore"]["Negative"]
    neu = response["SentimentScore"]["Neutral"]
    mix = response["SentimentScore"]["Mixed"]
    return {"sentiment": neu+mix}



async def get_lit_sent_score(text):
    """
    Takes in string of text
    Returns a dictionary of "spelling", "reading", "literacy", and "sentiment"
    """
    dic = get_literacy_score(text)
    sentiment = get_sentiment_score(text)
    dic.update(sentiment)
    return dic
