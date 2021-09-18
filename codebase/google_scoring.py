import logging

logger = logging.getLogger()
if logger.handlers:
    for handler in logger.handlers:
        logger.removeHandler(handler)
logging.basicConfig(level=logging.INFO)

def get_url_score(url):
    """
    Takes in a string that is URL.
    Returns dictionary with "url_score"
    """

    ## grading based on https://www.adfontesmedia.com/wp-content/uploads/2018/08/Media-Bias-Chart_4.0_8_28_2018-min-1024x791.jpg
    score_100 = ["straitstimes.com", "channelnewsasia.com", "businesstimes.com.sg", "shinmin.sg", \
                 "todayonline.com", "zaobao.com.sg", "wanbao.com.sg", "sg.news.yahoo.com", "apnews.com", "reuters.com", \
                 "bloomberg.com", "c-span.org", "latimes.com", "abcnews.go.com", "pbs.org", \
                 "cbsnews.com", "bbc.com/news", "nytimes.com", "nbcnews.com", \
                 "gov.sg", "whitehouse.gov", "wikipedia.com", "who.int", "lexology.com"]
    score_85 = ["tnp.sg", "asiaone.com", "mothership.sg", "onlinecitizenasia.com", "sbr.com.sg", \
                "independent.sg", "buzzfeednews.com", "wsj.com", "washingtonpost.com", "msn.com", \
                "theguardian.com", "economist.com", "newyorker.com", "aseanbriefing.com", "dollarsandsense.com"]
    score_70 = ["fortune.com", "time.com", "forbes.com", "businessinsider.com", "vanityfair.com", \
                "cnn.com", "ijr.com", "foreignpolicy.com", "msnbc.com", "norfolkdailynews.com", "pressofatlanticcity.com", \
                "vulcanpost.com"]
    score_55 = ["edition.cnn.com", "washingtontimes.com", "huffingtonpost.co.uk", \
                "singaporestar.com", "singaporenews.net", "weekender.com.sg"]
    score_40 = ["foxnews.com", "nypost.com", "dailymail.co.uk"]
    scoring_criteria = {1: score_100, 0.85: score_85, 0.70: score_70, 0.55: score_55, 0.40: score_40}

    for score in scoring_criteria:
        sites = scoring_criteria[score]
        for domain in sites:
            if domain in url:
                return {"url_score": score}
    return {"url_score": 0.1}


def get_date_score(date_string):
    """
    Takes in a string that is date.
    Returns dictionary with "date_score"
    """

    import datetime
    today = datetime.datetime.today()

    try:
        if date_string[-9:] == "hours ago" or date_string[-7:] == "day ago":
            article = datetime.datetime.today() - datetime.timedelta(days=1)
        elif date_string[-8:] == "days ago":
            days_ago = int(date_string[0])
            article = datetime.datetime.today() - datetime.timedelta(days=days_ago)
        else:
            article = datetime.datetime.strptime(date_string, "%b %d, %Y")

        difference = (today-article).total_seconds() /60/60/24/365
        score = 3/(difference+3) ## 1 year =0.75, 3 years = 0.5
    except:
        score = 0
        if date_string == "Factchecker":
            score = 1

    return {"date_score": score}


def compute_url_date_score(lst):
    """
    Takes in a list of dictionaries
    Returns new dictionary collating all into a dictionary of list
    """

    for dic in lst:
        url_list = dic["url"]
        date_list = dic["date"]
        url_score_list = []
        date_score_list = []

        for x in range(len(url_list)):
            url_score = get_url_score(url_list[x])["url_score"]
            url_score_list.append(url_score)
            date_score = get_date_score(date_list[x])["date_score"]
            date_score_list.append(date_score)

        dic["url_score"] = url_score_list
        dic["date_score"] = date_score_list
        logger.info("URL Scores = " + str(url_score_list))
        logger.info("Date Scores = " + str(date_score_list))

    new_dic = {"sentence_chunk":[],\
               "url":[],\
               "title":[],\
               "synopsis":[],\
               "date":[],\
               "relevance_score":[],\
               "url_score":[],\
               "date_score":[],\
               "google_score":[]}

    for dic in lst:
        new_dic["sentence_chunk"].append(dic["sentence_chunk"])
        new_dic["url"].extend(dic["url"])
        new_dic["title"].extend(dic["title"])
        new_dic["synopsis"].extend(dic["synopsis"])
        new_dic["date"].extend(dic["date"])
        new_dic["url_score"].extend(dic["url_score"])
        new_dic["date_score"].extend(dic["date_score"])
        new_dic["relevance_score"].extend(dic["relevance_score"])

    return new_dic



def compile_score(dic, dic2):
    """
    Takes in 2 dictionaries
    Returns combined dictionary with additional "indiv_result_score" and "google"
    """
    dic.update(dic2)
    relevance = dic["relevance_score"]
    url = dic["url_score"]
    date = dic["date_score"]
    result = []

    text = "- Unable to find"
    dic["url1"] = text
    dic["url2"] = text
    for x in range(len(dic["url_score"])):
        if dic["url_score"][x] >= 0.85:
        #  or dic["date"][x] == "Factchecker":
            if dic["url1"] == text:
                dic["url1"] = dic["url"][x]
            elif dic["url2"] == text and dic["url1"] != dic["url"][x]:
                dic["url2"] = dic["url"][x]

        # score = 0.5*int(relevance[x]) + 0.25*url[x] + 0.25*date[x]
        score = 0
        if relevance[x] == 1:
            score = (0.6*url[x] + 0.4*date[x]) * 1.5
        elif relevance[x] == 0:
            score = (0.6*url[x] + 0.4*date[x]) * 0.7
        if score > 1:
            score = 1
        result.append(score)

    # average_relevance = sum(relevance) / len(relevance)
    google_score = 0
    threshold = 0.6
    if len(result) == 0:
        google_score = 0.5
    else:
        average_result = sum(result) / len(result)
        if average_result >= threshold:
            google_score = ((average_result - threshold) / (1 - threshold) * 0.5) + 0.5
        else:
            google_score = (average_result / threshold) * 0.5

        # if average_relevance <= 0.2:
        #     google_score = sum(result) / len(result) * 0.2
        # elif average_relevance >= 0.7:
        #     google_score = sum(result) / len(result) * 1.1
        # else:
        #     google_score = 0.5 * sum(result) / len(result)

    dic["indiv_result_score"] = result
    dic["google"] = google_score
    return dic
