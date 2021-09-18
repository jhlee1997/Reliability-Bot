import os
import logging
import boto3
import botocore
import hashlib

# Logging is cool!
logger = logging.getLogger()
if logger.handlers:
    for handler in logger.handlers:
        logger.removeHandler(handler)
logging.basicConfig(level=logging.INFO)

def update_values(table, final_dic):
	current_date_time = final_dic["current_date_time"]
	chat_id = final_dic["chat_id"]
	raw_input = final_dic["raw_input"]

	# These are all the variables for scores
	spelling = str(final_dic["spelling"])
	reading = str(final_dic["reading"])
	literacy = str(final_dic["literacy"])
	sentiment = str(final_dic["sentiment"])
	url_score = str(final_dic["url_score"])
	relevance_score = str(final_dic["relevance_score"])
	date_score = str(final_dic["date_score"])
	indiv_result_score = str(final_dic["indiv_result_score"])
	google = str(final_dic["google"])

	# These are all the variables for AI improvement
	sentence_chunk = final_dic["sentence_chunk"]
	title = final_dic["title"]
	synopsis = final_dic["synopsis"]

	# Creates a megastring from input date used to create unique hash id
	megastring = str(current_date_time) + str(chat_id) + str(final_dic["raw_input"])
	mhasher = hashlib.sha256()
	mhasher.update(megastring.encode('utf-8'))
	hashid = mhasher.hexdigest()	# unique hash id produced

	# Stores data in table called 'TelegramTable' if it exists in dynamodb, using the hashid as the main key
	response = table.update_item(
	Key = {"hashid": hashid},
	UpdateExpression = 'SET {} = :val1, {} =:val2, {} = :val3, {} = :val4, {} = :val5, \
	{} = :val6, {} = :val7, {} = :val8, {} = :val9, {} = :val10, \
	{} = :val11, {} = :val12, {} = :val13, {} = :val14, {} = :val15'.format(\
		'current_date_time', 'chat_id', 'raw_input', 'spelling', 'reading', 'literacy', 'sentiment', \
		'url_score', 'relevance_score', 'date_score', 'indiv_result_score', 'google', \
		'sentence_chunk', 'title', 'synopsis'),
	ExpressionAttributeValues = {":val1": current_date_time, ":val2": chat_id,":val3": raw_input, \
		":val4": spelling,":val5": reading,":val6": literacy,":val7": sentiment, \
		":val8": url_score,":val9": relevance_score, ":val10": date_score, ":val11": indiv_result_score, ":val12": google, \
		":val13": sentence_chunk, ":val14": title, ":val15": synopsis})

def dynamo_call(final_dic):
	client = boto3.resource("dynamodb")
	TableName = "TelegramTable"
	table = client.Table(TableName)

	try:
		update_values(table, final_dic)
		logger.info("Table exists, values saved in dynamodb")
	except botocore.exceptions.ClientError as e:
		# Creates table Telegram Table if it doesn't exist in dynamodb
		if e.response["Error"]["Message"] == "Requested resource not found":
			logger.info("Table does not exist, creating table in dynamodb...")
			createtable = client.create_table(
				TableName = TableName,
				KeySchema = [
					{
						"AttributeName": 'hashid',
						"KeyType": "HASH"
						}
					],
				AttributeDefinitions = [
					{
						"AttributeName": "hashid",
						"AttributeType": "S"
						}
					],
				ProvisionedThroughput = {
	                'ReadCapacityUnits': 5,
	                'WriteCapacityUnits': 5
	            })
			update_values(table, final_dic)
			logger.info("Table created, values saved in dynamodb")
