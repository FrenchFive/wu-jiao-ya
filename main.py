# INITIALIZATION
from openai import OpenAI
import requests #to do some web requests
import random
from datetime import datetime, timedelta
import json
import os
import time
import tweepy

print('// -- WU RUNNING -- //')
WOEID = 2459115 #NEW YORK 2459115 - 1 is WorldWide
TEXT_LEN = 220

scrpt_dir = os.path.dirname(os.path.abspath(__file__))
ENV = os.path.join(scrpt_dir, "secret.env")
env_file = open(ENV, 'r')
env_data = env_file.readlines()
KEY_OPENAI = env_data[0].replace('\n','')

def parse(sen, TEXT_LEN):
    TEXT_LEN += 10
    phrases = sen.split('<--->')
    for i in range(len(phrases)):
        tweet = phrases[i].replace('\n', '')
        if len(tweet) >= TEXT_LEN:
            words = tweet.split()
            truncwords = []
            currentlen = 0
            for word in words:
                currentlen += len(word) + 1
                if currentlen <= TEXT_LEN:
                    truncwords.append(word)
                else:
                    break
            truncsen = ' '.join(truncwords)
            if len(truncsen) < len(tweet):
                truncsen += ' ...'
            tweet = truncsen
        
        phrases[i] = f'{tweet} ({i+1}/{len(phrases)})'
    
    return(phrases)

def post(tweets):
    api_key = 'YtgzL2PYz1qLZ4oM1f1CzgObA'
    api_secret = 'Md5H7yDrbPKx5uPWfK8xqJoHu3VkkUiIF3yYU9RdmDzdQv3DW0'
    bearer_token = r'AAAAAAAAAAAAAAAAAAAAAK1ZsgEAAAAAO%2BFf%2FiHSwbn1PYmce6wF3nEbUX8%3DgYUzG07dA7eKBSOiUnaQ8mZmsSkRbw8KfCuNcucBJZgYWOi6VL'
    access_token = '1763189663416909824-eaB3rkuF56kxZPMTnX7EUQLtYyAiVk'
    secret_token = 'eQIMXSMlwQZ1pe6p9jXoitGrSleGz4iPSG4CnoI6F6te2'

    client = tweepy.Client(bearer_token, api_key, api_secret, access_token, secret_token, return_type=requests.Response)
    auth = tweepy.OAuth1UserHandler(api_key, api_secret, access_token, secret_token)
    api = tweepy.API(auth)

    tweet = client.create_tweet(text=tweets[0])
    prev_id = tweet.json()['data']['id']
    print(f'- SENT TWEET : 1/{len(tweets)}')

    for t in range(1, len(tweets)):
        tweet = client.create_tweet(text=tweets[t], in_reply_to_tweet_id=prev_id)
        prev_id = tweet.json()['data']['id']
        print(f'- SENT TWEET : {t+1}/{len(tweets)}')

    print('-- DONE SENDING')

# OPENAI REQUEST FUNCTION
def generate(querys, files):
    #INITIALIZATION
    client = OpenAI(api_key=KEY_OPENAI)

    wu_id = "asst_sSfA6dWpfgeobpHJM44d9eIi"

    #UPLOAD FILES
    files_id = []
    print('-- UPLOADING FILES')
    for fi in files:
        if os.path.getsize(fi) > 100:
            file_data = client.files.create(
                file=open(fi , "rb"),
                purpose="assistants"
            )
            client.beta.assistants.files.create(
                assistant_id = wu_id,
                file_id = file_data.id
            )
            files_id.append(file_data.id)
    
    print('-- ALL FILES PROCESSED')

    #CREATE A THREAD
    thread = client.beta.threads.create()

    
    #MESSAGES
    for query in querys:
        client.beta.threads.messages.create(
            thread.id,
            role="user",
            content=query,
        )

    #RUN
    print('-- RUNNING')
    run = client.beta.threads.runs.create(
        thread_id=thread.id,
        assistant_id=wu_id
    )

    print('-- WAITING GEN')
    while True:
        run = client.beta.threads.runs.retrieve(thread_id=thread.id, run_id=run.id)
        if run.completed_at:
            print("-- GENERATED")
            break
    
    messages = client.beta.threads.messages.list(thread_id=thread.id)
    response = messages.data[0].content[0].text.value

    #DELETE FILES
    for fi_id in files_id:
        client.beta.assistants.files.delete(
            assistant_id = wu_id,
            file_id = fi_id
        )
        client.files.delete(fi_id)
    client.beta.threads.delete(thread.id)
    print('-- FILES and THREAD DELETED')

    return(response)

# VAR TO TXT
def to_txt(var, name):
    file_path = name + '.json'
    
    with open(file_path, 'w', encoding='utf-8') as file:
        json.dump(var, file, indent=2)
    
    print('-- STORED ::' + name)

# SEARCH TRENDS FUNCTION
def get_trends(woeid): #GET THE TRENDS FROM AN RAPIDAPI TWITTER API - CREATE A LIST AND WEIGHT
    url = "https://twitter154.p.rapidapi.com/trends/"
    querystring = {"woeid":woeid}
    headers = {
        "X-RapidAPI-Key": "61f3c0067fmsh0885929e7397a91p11fa14jsn26c12c35a544",
        "X-RapidAPI-Host": "twitter154.p.rapidapi.com"
    }
    response = requests.get(url, headers=headers, params=querystring)

    data = response.json()[0]
    #print(data)
    trends = data['trends']
    trends_list = []
    weight = []
    for trend in trends:
        if trend['promoted_content'] == None:
            trends_list.append(trend['name'])
            if trend['tweet_volume'] != None:
                weight.append(int(trend['tweet_volume']))
            else:
                weight.append(0)
    weight_max = max(weight)
    weight_min = min([num for num in weight if num != 0])
    weight = [num if num != 0 else weight_min for num in weight]
    target_min = 0.1
    target_max = 0.9
    normalized_weight = []
    for num in weight:
        normalized_number = ((num - weight_min) / (weight_max - weight_min)) * (target_max - target_min) + target_min
        normalized_weight.append(round(normalized_number,3))
    return(trends_list, normalized_weight)

# READ TWEETS FUNCTION
def gettweets(query):
    current_date = datetime.now().strftime('%Y-%m-%d')
    yesterday_date = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
    url = "https://twitter154.p.rapidapi.com/search/search"
    querystring = {"query":query,"section":"top","min_retweets":"10","min_likes":"100","limit":"50","start_date":yesterday_date,"language":"en"}
    headers = {
        "X-RapidAPI-Key": "61f3c0067fmsh0885929e7397a91p11fa14jsn26c12c35a544",
        "X-RapidAPI-Host": "twitter154.p.rapidapi.com"
    }
    response = requests.get(url, headers=headers, params=querystring)

    try:
        tweets = response.json()['results']
        tweets_list = []
        for tweet in tweets:
            dict_tweet = {}
            #dict_tweet['tweet_id'] = tweet["tweet_id"]
            dict_tweet['tweet'] = tweet['text']
            dict_tweet['user'] = tweet["user"]["username"]
            dict_tweet['time'] = tweet["creation_date"]

            tweets_list.append(dict_tweet)
        
        return(tweets_list)
    except:
        print("error")
        print(response.json())
        print(' ')
        return([])

#ARTICLE ANALYSIS
def article_analysis(article):
    url = "https://extract-news.p.rapidapi.com/v0/article"
    if article != '':
        url = "https://article-extractor2.p.rapidapi.com/article/parse"
        querystring = {"url":article}
        headers = {
            "X-RapidAPI-Key": "61f3c0067fmsh0885929e7397a91p11fa14jsn26c12c35a544",
            "X-RapidAPI-Host": "article-extractor2.p.rapidapi.com"
        }

        response = requests.get(url, headers=headers, params=querystring)
        try:
            if response.json()['error'] == 0:
                return(response.json()['data']['content'])
            else:
                return('None')
        except:
            print("error")
            print(response.json())
            print(' ')
            return('None')

# GOOGLE QUERY
def getnews(query):
    query = query.replace('#','')
    query = query.replace('-','')
    current_date = datetime.now().strftime('%d/%m/%Y')
    yesterday_date = (datetime.now() - timedelta(days=1)).strftime('%d/%m/%Y')
    url = "https://newsnow.p.rapidapi.com/newsv2"
    payload = {
        "query": query,
        "time_bounded": True,
        "from_date": yesterday_date,
        "to_date": current_date,
        "location": "us",
        "language": "en",
        "page": 10
    }
    headers = {
        "content-type": "application/json",
        "X-RapidAPI-Key": "61f3c0067fmsh0885929e7397a91p11fa14jsn26c12c35a544",
        "X-RapidAPI-Host": "newsnow.p.rapidapi.com"
    }

    response = requests.post(url, json=payload, headers=headers)

    news = response.json()['news']
    news_list = []

    for article in news:
        dict_artcl = {}
        dict_artcl['title'] = article['title']
        dict_artcl['short'] = article['short_description']
        dict_artcl['text'] = article['text']
        dict_artcl['date'] = article['date']
        dict_artcl['long'] = article_analysis(article['url'])
        news_list.append(dict_artcl)


    return(news_list)


time.sleep(2)
trends, weight = get_trends(WOEID)
to_txt(trends, "trends")
query_list = [
    'Provided with a file containing all trendings on Twitter in NewYork right now, choose 5 topics that would be the most interesting to do a thread on',
    'Only respond with the list of the topics you picked, all seperated by a comma : ,'
]
file_list=['trends.json']
gen_trend = generate(query_list, file_list)
print(f'POSSIBLE SUBJECTS : {gen_trend}')
trend_list = gen_trend.split(', ')
trend = str(random.choice(trend_list))
print('-- THE TREND WILL BE :: ' + trend)

time.sleep(2)
tweets = gettweets(trend)
to_txt(tweets, "tweets")
print(f'TWEET DATA SIZE :: {os.path.getsize("tweets.json")} bytes')

time.sleep(2)
print('-- SEARCHING FOR NEWS')
news = getnews(trend)
to_txt(news, "news")
print(f'SEARCH DATA SIZE :: {os.path.getsize("news.json")} bytes')

print(' ')
thread_lenght = random.randint(3,10)
query_gen_list = [
    f' Write a thread of {thread_lenght} tweets, each {TEXT_LEN} characters long, explaining what is going on about : {trend}, why are people talking about it, based on files provided ',
    'The first tweet is the most important, it must draws attention and questions the audience, so the user wants to read the rest of the thread',
    'Add as much detail and precision as you can, without inventing, and still maintaining it entertaining',
    'In your response : INCLUDE ONLY THE TWEETS AND EMOJIS, nothing else, do not count tweets, do not index them',
    'You NEED to seperate tweets using : <--->'
]
file_list = ['tweets.json', 'news.json']
gen = generate(query_gen_list, file_list)
print(gen)

parsed_tweet = parse(gen, TEXT_LEN)
to_txt(parsed_tweet, 'post')

post(parsed_tweet)