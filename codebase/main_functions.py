def validation(raw_text):
    """
    Takes in string of raw user input
    Returns dictionary of "validity" and "text".
    Text is response message if invalid, original raw input if valid.
    """

    # length check
    if len(raw_text) < 250:
        text = "Your input is too short! Please input about 1-2 paragraphs for a more accurate result."
        return {"validity": False, "text": text}
    if len(raw_text) > 4000:
        text = "Your input is way... too... long... Bot... breakdown... Just kidding! Just input something shorter please!"
        return {"validity": False, "text": text}

    # character check
    # for x in raw_text:
    #     if ord(x) > 127:
    #         text = "Non-English characters detected. Please remove all Chinese/Tamil characters or emojis. Thank you!"
    #         return {"validity": False, "text": text}

    return {"validity": True, "text": raw_text}

def create_reply(scores):
    '''
    Takes in dictionary of scores and URLs.
    Returns a string of response
    '''


    results = "Here are your results!\n\n" + \
    "Literacy Score = " + str(round(scores["literacy"]*100, 2)) + "%\n" + \
    "Sentiment Score = " + str(round(scores["sentiment"]*100, 2)) + "%\n" + \
    "Google Score = " + str(round(scores["google"]*100, 2)) + "%\n\n"

    # putting scores as true=high, false=low
    lit, sent, goog = False, False, False
    if scores["literacy"] > 0.5:
        lit = True
    if scores["sentiment"] > 0.5:
        sent = True
    if scores["google"] > 0.5:
        goog = True

    #constants
    high_literacy = "This piece of text looks very professionally written "
    low_literacy = "This piece of text does not look very professionally written "
    high_sentiment = " seems to give a neutral/balanced perspective. "
    low_sentiment = " seems to purposefully trigger strong emotions. "
    high_google = ", it appears to be sufficiently supported by credible sources. "
    low_google = ", it appears to be insufficiently supported by credible sources. "

    literacy = high_literacy if lit else low_literacy
    sentiment = high_sentiment if sent else low_sentiment
    google = high_google if goog else low_google
    conjunction1 = "and" if (lit == sent) else "but"
    conjunction2 = "Additionally" if(sent == goog) else "However"

    if (lit and sent and goog):
        recc = "This article seems well written and well supported!"
    elif (lit and (not sent or not goog)):
        recc = "Therefore, we recommend that you read this article with a pinch of salt and do further research to fully understand all sides of this story."
    elif (not lit and (sent or goog)):
        recc = "Hence, we recommend that you search up more articles from reputable sources to better understand the truths of this topic."
    else:
        recc = "This article is poorly written and poorly supported, it is very likely that this was created to spread false information. We highly recommend that you seek more articles from reputable sources for more reliable information. You can also send me new texts you find!"

    link_text = "\n\nHere are credible links that may be relevant:\n"
    url1 = scores["url1"] + "\n"
    url2 = scores["url2"]

    return results + literacy + conjunction1 + \
           sentiment + conjunction2 + google + \
           recc + link_text + url1 + url2
