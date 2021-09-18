from requests_html import HTMLSession
from lxml import etree
from bs4 import BeautifulSoup
import re
import boto3
import logging

# Testing purposes
# raw = {"validity": True, "text": "Just now, the US CNBC website reported that several US Growler electronic warplanes were mysteriously attacked when they flew to the South China Sea again. These warplanes were all out of control midway, but these warplanes were out of control for only a few seconds. Then the US military ordered the request. All fighters over the South China Sea withdrew."}

logger = logging.getLogger()
if logger.handlers:
    for handler in logger.handlers:
        logger.removeHandler(handler)
logging.basicConfig(level=logging.INFO)

stop_words = ["i", "me", "my", "myself", "we", "our", "ours", "ourselves", "you", "your", "yours", "yourself", "yourselves", "he", "him", "his", "himself", "she", "her", "hers", "herself", "it", "its", "itself", "they", "them", "their", "theirs", "themselves", "what", "which", "who", "whom", "this", "that", "these", "those", "am", "is", "are", "was", "were", "be", "been", "being", "have", "has", "had", "having", "do", "does", "did", "doing", "a", "an", "the", "and", "but", "if", "or", "because", "as", "until", "while", "of", "at", "by", "for", "with", "about", "against", "between", "into", "through", "during", "before", "after", "above", "below", "to", "from", "up", "down", "in", "out", "on", "off", "over", "under", "again", "further", "then", "once", "here", "there", "when", "where", "why", "how", "all", "any", "both", "each", "few", "more", "most", "other", "some", "such", "no", "nor", "not", "only", "own", "same", "so", "than", "too", "very", "s", "t", "can", "will", "just", "don", "should", "now"]

def process_data_function(raw_data):
    """
    Helper function for webscraper_function
    Takes in raw user input (string) and returns a list of tuples containing (2-sentence-chunk, search query)
    """
    # Break up into 2-sentence-chunks
    raw_sentences = re.split(r"[.!?]", raw_data)
    raw_sentences = [sentence.strip(" ") for sentence in raw_sentences]
    raw_sentences = [sentence.strip("\n") for sentence in raw_sentences]
    del raw_sentences[-1]
    raw_sentences = [sentence + "." for sentence in raw_sentences]

    sentence_chunk_search_query_tuples = []
    for i in range(len(raw_sentences) - 1):
        sentence_chunk = raw_sentences[i] + " " + raw_sentences[i + 1]
        comprehend = boto3.client(service_name='comprehend', region_name='us-east-1')
        # TODO: Run each chunk through AWS comprehend sentiment analysis (to check negation)
        # comprehend.detect_sentiment(Text=sentence_chunk, LanguageCode='en')
        keywords_dict = comprehend.detect_key_phrases(Text=sentence_chunk, LanguageCode='en')
        keywords_list = keywords_dict["KeyPhrases"]
        keywords_list.sort(key = lambda x:x["Score"],reverse = True)
        aws_keyphrases = ""
        aws_keywords = []
        for dict in keywords_list:
            aws_keyphrases += dict["Text"].lower() + " "
        aws_keywords = aws_keyphrases.split()
        filtered_words = [w for w in aws_keywords if not w in stop_words]
        search_query = "+".join(filtered_words)
        sentence_chunk_search_query_tuples.append((sentence_chunk, search_query))
    return sentence_chunk_search_query_tuples

def webscraper_function(raw_data):
    """
    Takes in raw user input (string), and returns a list of dictionaries.
    Each dictionary contains results for a google search, and is in the format
    {"sentence_chunk" : <String containing 2-sentence-chunk>,
    "url" : [List of URLs],
    "title" : [List of search result titles],
    "synopsis" : [List of search result synopses],
    "date" : [List of each search result dates]}
    """
    processed_data = process_data_function(raw_data)
    google_search_list = []
    for (sentence_chunk, search_query) in processed_data:
        # preprocessed_query = "\"" + search_query + "\""
        url = 'https://www.google.com/search?q={}&tbs=cdr:1,cd_min:1/1/0'.format(search_query)
        logger.info("URL Searched = " + str(url))
        # print(url + '\n')
        # print('#############################################\n')

        # Open a HTMLSession to execute JavaScript code to fully render webpage
        with HTMLSession() as session:
            r = session.get(url)

        # Input this HTML Object into BeautifulSoup to parse and access individual tags and their text content
        soup = BeautifulSoup(r.text, 'html.parser')

        # center = soup.find('div', id='center_col')

        articles = soup.find_all('div', class_='rc')

        temp_dict = {}
        temp_dict["sentence_chunk"] = sentence_chunk
        temp_dict["url"] = []
        temp_dict["title"] = []
        temp_dict["synopsis"] = []
        temp_dict["date"] = []

        for article in articles:
            header = article.find('div', class_='r').find('a', href=True)
            link = header['href']
            title = header.find('h3').text
            title = re.sub('\s\.\.\.$', '', title)
            date = ""
            try:
                synopsis = article.find('span', class_='st').text

                if re.search('^[a-zA-Z]+\s\d+,\s\d+', synopsis):
                    date = re.findall('^[a-zA-Z]+\s\d+,\s\d+', synopsis)[0]
                    synopsis = re.sub('^[a-zA-Z]+\s\d+,\s\d+ - ', '', synopsis)
                    synopsis = re.sub('\s\.\.\.$', '', synopsis)
                elif re.search('^\d+\s[a-zA-Z]+\s[a-zA-Z]+', synopsis):
                    date = re.findall('^\d+\s[a-zA-Z]+\s[a-zA-Z]+', synopsis)[0]
                    synopsis = re.sub('^\d+\s[a-zA-Z]+\s[a-zA-Z]+ - ', '', synopsis)
                    synopsis = re.sub('\s\.\.\.$', '', synopsis)
            except:
                synopsis = article.find('div', class_='P1usbc').text    # Factchecker's 'synopsis' (Claim + Claim by who + Factcheck done by who + Rating of truthfulness)
                date = "Factchecker"    # Indicates that this is a factchecker response
            temp_dict["url"].append(link)
            temp_dict["title"].append(title)
            if len(synopsis) > 0:
                temp_dict["synopsis"].append(synopsis)
            else:
                temp_dict["synopsis"].append(".")
            temp_dict["date"].append(date)
        google_search_list.append(temp_dict)

    # Testing purposes
    # for dictionary in google_search_list:
    #     for key, value in dictionary.items():
    #         print(key)
    #         print(value)

    return google_search_list
        # TODO: pass up 1 or 2 credible sources to main telegram script

# webscraper_function(raw)
