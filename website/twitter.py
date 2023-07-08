import json

import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
from flask import Blueprint, render_template, request, redirect, url_for
from flask_login import current_user, login_required
import requests
import io
import base64
import mpld3
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from IPython.display import display
from flask import jsonify
import ccxt
from datetime import datetime, timedelta
#from . import db
#from . modules import User


import datetime as DT


# Set up default dates to be fron 90 days ago till today
today = DT.date.today()
two_week_ago = str(today - DT.timedelta(days=14))
today = str(today)

def gen_sent_graph_nasdaq(coin_symbol, start_date,end_date):
    return




def gen_sent_graph_twitter(coin_symbol, start_date, end_date):
    import json
    from twython import TwythonStreamer, Twython
    import csv
    import pandas as pd
    import matplotlib.pyplot as plt
    import nltk
    dler = nltk.downloader.Downloader()
    dler._update_index()
    dler.download('popular', quiet=True)
    from nltk.corpus import wordnet as wn

    # Credentials we've got through twitter
    credentials = {}
    credentials['CONSUMER_KEY'] = 'ZLn6F7PRT8s5ZJgzkFBt6pkMB'
    credentials['CONSUMER_SECRET'] = 'wGCvBFK9GLpVR277TkjPkINCa0e37rNjY93pPRvNJS1vdTGr5e'
    credentials['ACCESS_TOKEN'] = '1314201877546901506-9uHbSbBBxiSRL26x3Bh2RRD9x7iVmO'
    credentials['ACCESS_SECRET'] = 'azdziHOFiKxvbld8yfNqDoQDdZvdXpbRPbmlOK2cFXAIB'

    # Save the credentials object to file
    with open("twitter_credentials.json", "w") as file:
        json.dump(credentials, file)

    # Load credentials from json file
    with open("twitter_credentials.json", "r") as file:
        creds = json.load(file)

        # Instantiate an object
    python_tweets = Twython(creds['CONSUMER_KEY'],
                            creds['CONSUMER_SECRET'],
                            creds['ACCESS_TOKEN'],
                            creds['ACCESS_SECRET'])

    # Set up our query parameters based on user input
    search1 = coin_symbol
    slang = 'en'
    scount = 10000
    TimeSearch = start_date
    TimeSearchEnd = end_date

    # Create our query
    query = {'q': search1,
             # 'result_type': 'popular',
             'count': scount,
             'lang': slang,
             'since': TimeSearch,
             'until': TimeSearchEnd,
             }

    # Search tweets for tweets mentioning coin symbol
    dict_ = {'user': [], 'date': [], 'text': [], 'favorite_count': []}
    for status in python_tweets.search(**query)['statuses']:
        dict_['user'].append(status['user']['screen_name'])
        dict_['date'].append(status['created_at'])
        dict_['text'].append(status['text'])
        dict_['favorite_count'].append(status['favorite_count'])

    # Structure data in a pandas DataFrame for easier manipulation
    # And sorts it by favorite count of each Tweet
    df = pd.DataFrame(dict_)
    df.sort_values(by='favorite_count', inplace=True, ascending=False)
    df.sort_values(by='favorite_count')

    # Create list of words associated with buy/sell/hold
    buy_words = ["long", "outperform", "buy", "sector perform", "hot", "bulles","undervalued","growth potential","attractive valuation","market leading position","strong fundamentals","bullish", "overweight", "positive",
                 "strong buy", "great", "awesome", "recommended"]
    sell_words = ["sell", "underperform", "underweight", "underwt/in-Line", "frozen", "bleeding", "reduce", "sucks",
                  "weak competitive position","high debt levels","bearish","underperform","Overvalued","negative catalysts","throw", "trash", "short"]
    holding_words = ["hold", "neutral", "market perform", "wait and see", "wait", "balanced risk", "balanced","balanced reward","limited upside",
                     "limited downside", "stable performance", "market uncertain", "in-line","moderate growth prospects"]


    # For each word in the buy words list - add it's synonyms to the list
    # Repet for sell and hold words
    arr = []
    for word in buy_words:
        for syn in wn.synsets(word):
            arr.append(syn.name().split('.')[0])
    buy_words += arr
    arr = []
    for word in sell_words:
        for syn in wn.synsets(word):
            arr.append(syn.name().split('.')[0])
    sell_words += arr
    arr = []
    for word in holding_words:
        for syn in wn.synsets(word):
            arr.append(syn.name().split('.')[0])
    holding_words += arr


    # Erase duplicates from list
    buy_words = list(set(buy_words))
    sell_words = list(set(sell_words))
    holding_words = list(set(holding_words))

    # (Weighted) counters for each operation
    c_buy = 0
    c_sell = 0
    c_hold = 0

    # The tweet with the most likes is fetched
    # Will be used later to normalize the weight of each tweet
    max_fav = df.iloc[0]['favorite_count']
    df = df.reset_index()

    # Calculate coin operations by their weights
    for index, row in df.iterrows():
        # the tweet with the most likes gets a weight of 1,
        # the rest are weighed in relation to that
        weight = row['favorite_count'] / max_fav
        # put the value of a tweet in [1,2] range
        val = 1 + weight
        # the tweet text itself
        text = row['text']
        # split into words
        txt_arr = text.split(' ')
        for word in txt_arr:
            word = word.lower()
            if word in buy_words:
                # if a tweet contains a words associated with buying,
                # we count it as a "buy tweet", same for sell and hold
                c_buy += val
                break
            if word in sell_words:
                c_sell += val
                break
            if word in holding_words:
                c_hold += val
                break
        # Set up and plot the results as a bar graph

    # total buy/sell/hold mentions in tweets with weight taken into account
    total = c_buy + c_sell + c_hold
    y_temp = [c_buy, c_sell, c_hold]
    x_axis = ['Buy', 'Sell', 'Hold']
    x_axis_categories_values = [c_buy, c_sell, c_hold]
    if total == 0:
        percentages = [0, 0, 0]
    else:
        percentages = [(sentiment / total) * 100 for sentiment in x_axis_categories_values]
    data = {
    "coin name":coin_symbol,
    "percentages": percentages,
    "x_axis": x_axis,
    "x_axis_categories_values": x_axis_categories_values
    }

    json_data = json.dumps(data)
   
    return json_data


def run_coin_twitter(list_coin_symbol, start_date=two_week_ago, end_date=today):
    coins = []
    num_of_coins =4# len(list_coin_symbol)
    #for i in range(4):
    for symbol in list_coin_symbol:
        coin_data = get_data_on_coin(symbol, start_date, end_date)
        coins.append(coin_data)
    return coins

def get_data_on_coin(symbol, start_date, end_date):
    coin = []
    word_json = {}
    word__json_array = []
    percentages = [0,0,0]
    x_axis_categories_values = [0,0,0]
    keywords = convert_symbol_to_keywords(symbol)
    for word in keywords:
        word_json = gen_sent_graph_twitter(word, start_date, end_date)
        word__json_array.append(word_json)
    for json_data in word__json_array:
        json_data = json.loads(json_data)
        x_axis_categories_values[0] += json_data.get("x_axis_categories_values", [])[0]
        x_axis_categories_values[1] += json_data.get("x_axis_categories_values", [])[1]
        x_axis_categories_values[2] += json_data.get("x_axis_categories_values", [])[2]
        

    total = x_axis_categories_values[0] + x_axis_categories_values[1] + x_axis_categories_values[2]
    percentages[0] = (x_axis_categories_values[0] / total) * 100
    percentages[1] = (x_axis_categories_values[1] / total) * 100
    percentages[2] = (x_axis_categories_values[2] / total) * 100

    return {'coin name': symbol, 'percentages': percentages, 'x_axis': ['Buy','Sell','Hold'], 'x_axis_categories_values': x_axis_categories_values}

def convert_symbol_to_keywords(symbol):
    keywords = []
    if symbol == 'ETH':
        keywords = ['#ETHUSD', 'ETH', 'Ethereum', '#ETH', 'ETHUSD', '#Ether']
    elif symbol == 'USDT':
        keywords = ['#USDTUSD', 'USDT', '#USDT', 'USDTUSD']
    elif symbol == 'BTC':
        keywords = ['#BTCUSD', 'Bitcoin', '#BTC', 'BTCUSD']
    elif symbol == 'ADA':
        keywords = ['#ADAUSD', '#ADAUSDT', '#ADA', 'ADAUSD']
    elif symbol == 'XRP':
         keywords = ['#XRPUSD', '#XRPUSDT', '#XRP', 'XRPUSD']
    elif symbol == 'DOGE':
          keywords = ['#DOGEUSD', '#DOGEUSDT', '#DOGE', 'DOGEUSD']
    elif symbol == 'DOT':
        keywords = ['#DOTUSD', '#DOTUSDT', '#DOT', 'DOTUSD']
    elif symbol == 'UNI':
        keywords = ['#UNIUSD', '#UNIUSDT', '#UNI', 'UNIUSD']
    elif symbol == 'ICP':
        keywords = ['#ICPUSD', '#ICPUSDT', '#ICP', 'ICPUSD']
    elif symbol == 'BCH':
        keywords = ['#BCHUSD', '#BCHUSDT', '#BCH', 'BCHUSD']
    elif symbol == 'LTC':
        keywords = ['#LTCUSD', '#LTCUSDT', '#LTC', 'LTCUSD']
    elif symbol == 'LINK':
        keywords = ['#LINKUSD', '#LINKUSDT', '#LINK', 'LINKUSD']
    elif symbol == 'MATIC':
        keywords = ['#MATICUSD', '#MATICUSDT', '#MATIC', 'MATICUSD']
    elif symbol == 'SOL':
        keywords = ['#SOLUSD', '#SOLUSDT', '#SOL', 'SOLUSD']
    elif symbol == 'ETC':
        keywords = ['#ETCUSD', '#ETCUSDT', '#ETC', 'ETCUSD']
    elif symbol == 'XLM':
        keywords = ['#XLMUSD', '#XLMUSDT', '#XLM', 'XLMUSD']
    elif symbol == 'THETA':
        keywords = ['#THETAUSD', '#THETAUSDT', '#THETA', 'THETAUSD']
    elif symbol == 'VET':
        keywords = ['#VETUSD', '#VETUSDT', '#VET', 'VETUSD']
    elif symbol == 'EOS':
        keywords = ['#EOSUSD', '#EOSUSDT', '#EOS', 'EOSUSD']
    elif symbol == 'BNB':
        keywords = ['#BNBUSD', '#BNBUSDT', '#BNB', 'BNBUSD']

    return keywords
    



def run_coin_nasdaq(list_coin_symbol, start_date=two_week_ago, end_date=today):
    plot_data = []
    api_key = '6P03OIQGX3TR7PH1'
    coins =[]
    fig, axs = plt.subplots(nrows=len(list_coin_symbol), ncols=1, figsize=(10, 10))
    for i, symbol in enumerate(list_coin_symbol):
        url = f'https://www.alphavantage.co/query?function=TIME_SERIES_DAILY_ADJUSTED&symbol={symbol}&apikey={api_key}&outputsize=full'
        response = requests.get(url)
        prices = []
        dates = []
        data = json.loads(response.content.decode('utf-8'))
        timeseries = data['Time Series (Daily)']

        for date in sorted(timeseries.keys()):
            if date >= start_date and date <= end_date:
                dates.append(date)
                prices.append(float(timeseries[date]['4. close']))
                
        
        {"name": symbol,"dates": dates, "prices": prices}
        coins.append({"name": symbol,"dates": dates, "prices": prices})
  
    return coins

    #return render_template('coins.html', image=image)


def get_historical_data(symbol_list):
    exchange = ccxt.binance()
    coins = []
    timeframe = '1d'
    today = datetime.now()
    start_date = today - timedelta(days=365)
    end_date = today
    start_date_timestamp = int(start_date.timestamp() * 1000)
    end_date_timestamp = int(end_date.timestamp() * 1000)

    for symbol in symbol_list:
        convert_symbol = symbol + '/USDT'
        historical_data = exchange.fetch_ohlcv(convert_symbol, timeframe, start_date_timestamp, end_date_timestamp)

        # Extract dates and prices from historical data
        dates = [datetime.fromtimestamp(item[0] / 1000) for item in historical_data]
        prices = [item[4] for item in historical_data]  # Closing prices

        coins.append({"name": symbol, "dates": dates, "prices": prices})

    return coins
    



twitter = Blueprint('twitter', __name__)
@twitter.route('/twitter', methods=['GET','POST'])
@login_required
def twitter_nlp():
    list = []
    coins = []
    if request.method == 'POST':
        coin_name_1 = request.form['cryptoCoin1']
        coin_name_2 = request.form['cryptoCoin2']
        coin_name_3 = request.form['cryptoCoin3']
        coin_name_4 = request.form['cryptoCoin4']
        # #BTC , Bitcoin, #BTCUSDT , BTCUSD
        coin_names = [coin_name_1, coin_name_2, coin_name_3, coin_name_4]
        for coin in coin_names:
            if coin.strip():  # Skip if coin is an empty string or contains only whitespace
                coins.append(coin)
        #list.append(coin_name_1)
        #list.append(coin_name_2)
        #list.append(coin_name_3)
        #list.append(coin_name_4)

        #historic_data = run_coin_nasdaq(list)
        historic_data = get_historical_data(coins)
        data_twitter = run_coin_twitter(coins)
        json_obj = {}
        
        for i, coin in enumerate(data_twitter, start=1):
            coin_name_key = f'coin_name_{i}'
            coin_dates_key = f'coin_dates_{i}'
            coin_prices_key = f'coin_prices_{i}'
            percentages_key = f'percentages_{i}'
            x_axis_key = f'x_axis_{i}'
            x_axis_categories_values_key = f'x_axis_categories_values_{i}'

            json_obj[coin_name_key] = coin['coin name']
            json_obj[coin_dates_key] = historic_data[i - 1]['dates']
            json_obj[coin_prices_key] = historic_data[i - 1]['prices']
            json_obj[percentages_key] = coin['percentages']
            json_obj[x_axis_key] = coin['x_axis']
            json_obj[x_axis_categories_values_key] = coin['x_axis_categories_values']
        json_obj['num_of_coins'] = len(data_twitter)
        return render_template('charts.html', user=current_user, plot_data=json_obj)                                           
    else:
        return render_template('twitter.html', user=current_user)
    
     #render_template('charts.html', user=current_user, plot_data=json_obj) #jsonify(json_obj) #render_template('charts.html', user=current_user, plot_data=json_array)
@twitter.route('/charts', methods=['GET'])
@login_required
def charts():
    return render_template('charts.html', user=current_user)
