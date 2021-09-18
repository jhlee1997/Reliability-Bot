import json
import telegram
import os
import logging
import asyncio

from main_functions import *
from literacy_sentiment import *
from webscraper import *
from ai import *
from google_scoring import *
from dynamo_call import *

# Logging is cool!
logger = logging.getLogger()
if logger.handlers:
    for handler in logger.handlers:
        logger.removeHandler(handler)
logging.basicConfig(level=logging.INFO)

OK_RESPONSE = {
    'statusCode': 200,
    'headers': {'Content-Type': 'application/json'},
    'body': json.dumps('ok')
}
ERROR_RESPONSE = {
    'statusCode': 400,
    'body': json.dumps('Oops, something went wrong!')
}

def configure_telegram():
    """
    Configures the bot with a Telegram Token.

    Returns a bot instance.
    """

    TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN')
    if not TELEGRAM_TOKEN:
        logger.error('The TELEGRAM_TOKEN must be set')
        raise NotImplementedError

    return telegram.Bot(TELEGRAM_TOKEN)

def set_webhook(event, context):
    """
    Sets the Telegram bot webhook.
    """

    logger.info('Event: {}'.format(event))
    bot = configure_telegram()
    url = 'https://{}/{}/'.format(
        event.get('headers').get('Host'),
        event.get('requestContext').get('stage'),
    )
    webhook = bot.set_webhook(url)

    if webhook:
        return OK_RESPONSE

    return ERROR_RESPONSE

def webhook(event, context):
    """
    Runs the Telegram webhook.
    """


    bot = configure_telegram()
    logger.info('Event: {}'.format(event))

    if event.get('httpMethod') == 'POST' and event.get('body'):
        logger.info('Message received')
        update = telegram.Update.de_json(json.loads(event.get('body')), bot)
        chat_id = update.message.chat.id
        message = update.message.text
        current_date_time = str(update.message.date)

        # NOTE: MIGHT NEED TO ASYNC THIS
        response = handle_message(message, chat_id, current_date_time)          # Process message and format a response
        # response = "ok"                           # Failsafe
        bot.sendMessage(chat_id = chat_id, text = response)
        logger.info('Message sent')

        return OK_RESPONSE

    return ERROR_RESPONSE

def handle_message(message, chat_id, current_date_time):
    """
    Process a message from Telegram
    """

    # Command Responses (tested)
    start_message = \
    "I am the @ReliabilityBot! Ever wondered if an article that a friend or relative has sent you can be trusted? \
Just copy and paste it into me and I will tell you what I think of it!\n\n\
To find out more about how I work, type /aboutreliabilitybot"

    help_message = \
    "Simply copy and paste a message or article you recieve for me to analyse!\n\n\
I have also found some useful tips to help you to better judge the reliability information in future:\n\
- https://www.gov.sg/article/singapores-fight-against-fake-news-what-you-can-do \n\
- https://sure.nlb.gov.sg/blog/fake-news/fn0006 \n\
- https://www.betterinternet.sg/-/media/MLC/Files/SID-2018/Quick-Tips/1_How-to-spot-Fake-News_Tipsheet.pdf"

    aboutReliabilityBot_message = \
    "Judgement Criteria:\n\
1. /aboutliteracy - This shows how sophisticated the piece of text is. More sophisticated articles are more likely to be reliable!\n\n\
2. /aboutsentiment - Indication of the text's overall objectivity. Balanced and unbiased articles are be more reliable!\n\n\
3. /aboutgooglesearch - This is an estimate of how well supported the text is by online articles. Greater corroboration = higher reliability!"

    aboutLiteracy_message = \
    "Literacy Score:\n\
I will be using a spell checker and a reading level estimator. \
The spell checker would flag misspelled words and produce a spelling score. \
The reading level estimator is an AI that estimates the age required to understand the text. \
I will then combine both results to determine the Literacy Score."

    aboutSentiment_message = \
    "Sentiment Score:\n\
I will ask my friend AWS Comprehend, another AI that uses Machine Learning and Natural Language Processing for sentiment analysis. \
Comprehend usually organises customer feedback on online shopping sites, but this time, she will tell me the sentiment of your input. \
A confidence score of Positive, Negative, Neutral, and Mixed will be given. \
I will then combine the Neutral and Mixed confidence to produce the Sentiment Score. Thanks Comprehend!!"

    aboutGoogleSearch_message = \
    "Google Search Score:\n\
I determine this score in a few steps. \
Firstly, I will conduct a Google Search using your input. \
Next, another unamed AI will help me to compare the results against your input to determine the extent of corroboration. \
In addition, I will determine the reliability and currency of the results based on its URL and date. \
Finally, after I consider all the factors, I will give you the Google Search Score."

    invalid_command = \
"Invalid command. Valid commands are /start /help /aboutreliabilitybot /aboutliteracy /aboutsentiment /aboutgooglesearch"

    # Command Handlers (tested)
    if message == "/start":
        return start_message
    elif message == "/help":
        return help_message
    elif message == "/aboutreliabilitybot":
        return aboutReliabilityBot_message
    elif message == "/aboutliteracy":
        return aboutLiteracy_message
    elif message == "/aboutsentiment":
        return aboutSentiment_message
    elif message == "/aboutgooglesearch":
        return aboutGoogleSearch_message
    elif message[0] == "/":
        return invalid_command

    # Validation Check (tested)
    valid = validation(message)
    if not valid["validity"]:
        return valid["text"]

    # Webscraper. Returns list of dictionaries, with each dictionary in the format of
    # {"sentence_chunk" : <String containing 2-sentence-chunk>,
    # "url" : [List of URLs],
    # "title" : [List of search result titles],
    # "synopsis" : [List of search result synopses],
    # "date" : [List of each search result dates]} (tested)
    webscraper_list = webscraper_function(message)

    # AI. Returns a list of dictionaries with additional key
    # {"relevance_score": [List of relevance scores]}

    # NOTE: ASYNC AI FUNCTION
    # ai_output_list = ai_function(webscraper_list)
    # ai_task = asyncio.create_task(ai_function(webscraper_list)) 
    # ai_output_list = await ai_task
    
    # Literacy and Sentiment Analysis. Returns dictionary {"spelling", "reading", "literacy", "sentiment"} (tested)

    # NOTE: ASYNC GET LITERACY SCORE
    # lit_sent_dic = get_lit_sent_score(message)
    # lit_sent_task = asyncio.create_task(get_lit_sent_score(message))
    # lit_sent_dic = await lit_sent_task

    async def async_function(loop):
        tasks = []
        logger.info("Task list created")
        tasks.append(asyncio.ensure_future(ai_function(webscraper_list),loop=loop))
        tasks.append(asyncio.ensure_future(get_lit_sent_score(message),loop=loop))
        results_lst = await asyncio.gather(*tasks)
        
        return results_lst

    loop = asyncio.get_event_loop()
    ai_lit_sent_results = loop.run_until_complete(async_function(loop))

    #ai_lit_sent_results = asyncio.run(async_function())
    ai_output_list = ai_lit_sent_results[0]
    lit_sent_dic = ai_lit_sent_results[1]

    # # Placeholder values for AI scores
    # # for dic in webscraper_list:
    # #     dic["relevance_score"] = [0.78, 0.74, 0.72, 0.73, 0.69, 0.66, 0.70, 0.67, 0.65, 0.65]
    # # ai_output_list = webscraper_list
    
    google_dic = compute_url_date_score(ai_output_list)

    # # Final scores
    final_dic = compile_score(lit_sent_dic, google_dic)

    # # Preparing final_dic for dynamo call
    final_dic["chat_id"] = chat_id
    final_dic["raw_input"] = message
    final_dic["current_date_time"] = current_date_time
    dynamo_call(final_dic)

    # # Personalised response
    response = create_reply(final_dic)

    return response
