import praw
import yfinance as yf
from flask import Blueprint, render_template, request
from flask_login import login_required, current_user
from praw import Reddit
import pandas as pd
import matplotlib.pyplot as plt
import nltk
from nltk.corpus import wordnet as wn
from datetime import datetime
import datetime as DT
import requests
import io
import json
import base64
import ccxt
from datetime import datetime, timedelta
today = DT.date.today()
ten_days_ago = str(today - DT.timedelta(days=10))
today = str(today)

def gen_sent_graph_reddit(coin_symbol, start_date, end_date):
    nltk.download('popular', quiet=True)

    # Credentials for accessing the Reddit API
    client_id = 'H5oV_TU5abuhE4VL2z5yiQ'
    client_secret = 'q3TEHvIlEsaF-QVCUaD5DkdiU7GP-g'
    user_agent = 'reddit_stocks'
    username = 'ddd_3333'
    password = '321747388Dp'

    reddit = praw.Reddit(client_id=client_id, client_secret=client_secret, user_agent=user_agent, username=username,
                         password=password, check_for_async=False)

    # Specify the date range
    date_format = '%Y-%m-%d'
    start_date = datetime.strptime(start_date, date_format)
    end_date = datetime.strptime(end_date, date_format)

    # Get all stock name variations
    names =coin_symbol# list(coin_symbol.values())

    # Query parameters
    search_query = ' OR '.join(names)
    subreddit_to_search = ['stocks', 'trading', 'stockmarket', 'investing']

    posts = []

    # Search the subreddit
    for subreddit in subreddit_to_search:
        subreddit_instance = reddit.subreddit(subreddit)
        sub_posts = subreddit_instance.search(query=search_query,
                                              sort='top',
                                              time_filter='all',
                                              limit=100000)
        posts += sub_posts

    filtered_posts = []

    for post in posts:
        # for post in sub:
        if start_date <= datetime.fromtimestamp(post.created_utc) <= end_date:
            filtered_posts.append(post)

    # Create pandas DataFrame
    dict_ = {'user': [], 'date': [], 'title': [], 'content': [], 'upvotes': []}
    for post in filtered_posts:
        dict_['user'].append(post.author.name)
        dict_['date'].append(post.created_utc)
        dict_['title'].append(post.title)
        dict_['content'].append(post.selftext)
        dict_['upvotes'].append(post.score)

    # Sort it by upvotes
    df = pd.DataFrame(dict_)
    df.sort_values(by='upvotes', inplace=True, ascending=False)
    # display(df)

    buy_words = ["long", "outperform", "buy", "sector perform", "hot", "bulles", "undervalued", "growth potential",
                 "attractive valuation", "market leading position", "strong fundamentals", "bullish", "overweight",
                 "positive", "strong buy", "great", "awesome", "recommended"]
    sell_words = ["sell", "underperform", "underweight", "underwt/in-Line", "frozen", "bleeding", "reduce", "sucks",
                  "weak competitive position", "high debt levels", "bearish", "underperform", "Overvalued",
                  "negative catalysts", "throw", "trash", "short"]
    holding_words = ["hold", "neutral", "market perform", "wait and see", "wait", "balanced risk", "balanced",
                     "balanced reward", "limited upside", "limited downside", "stable performance",
                     "market uncertain", "in-line", "moderate growth prospects"]

    # Lists of words comparable with buy/sell/hold
    # buy_words = ["long","outperform", "buy", "sector perform", "hot", "bulles","overweight", "positive", "strong buy","great","awesome","recommended"]
    # sell_words = ["sell", "underperform", "underweight", "underwt/in-Line", "frozen", "bleeding", "reduce","sucks","throw","trash","short"]
    # holding_words = ["hold", "neutral", "market perform"]

    # Add synonyms to the word lists
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

    # Remove duplicates from the lists
    buy_words = list(set(buy_words))
    sell_words = list(set(sell_words))
    holding_words = list(set(holding_words))

    # for percentage pie chart
    p_buy = 0
    p_sell = 0
    p_hold = 0

    max_upvotes = df['upvotes'].max()

    # Calculate sentiment scores based on upvotes and word associations
    for _, row in df.iterrows():
        val_p = 1 + row['upvotes']
        text = row['title'] + " " + row['content']
        txt_arr = text.lower().split(' ')
        for word in txt_arr:
            if word in buy_words:
                p_buy += val_p
                break
            if word in sell_words:
                p_sell += val_p
                break
            if word in holding_words:
                p_hold += val_p
                break

    # Get the maximum number of upvotes for normalization
    total = p_buy + p_sell + p_hold

    y_temp = [p_buy, p_sell, p_hold]
    x_axis = ['Buy', 'Sell', 'Hold']
    x_axis_categories_values = [p_buy, p_sell, p_hold]
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


def convert_symbol_to_keywords(symbol):
    keywords = []
    if symbol == 'ETH':
        keywords = ['#ETHUSD', 'ETH', 'Ethereum', '#ETH']
    elif symbol == 'USDT':
        keywords = ['#USDTUSD', 'USDT', '#USDT', 'USDT']
    elif symbol == 'BTC':
        keywords = ['#BTCUSD', 'Bitcoin', '#BTC', 'BTC']
    elif symbol == 'ADA':
        keywords = ['#ADAUSD', '#ADAUSDT', '#ADA', 'ADA']
    elif symbol == 'XRP':
         keywords = ['#XRPUSD', '#XRPUSDT', '#XRP', 'XRP']
    elif symbol == 'DOGE':
          keywords = ['#DOGEUSD', '#DOGEUSDT', '#DOGE', 'DOGE']
    elif symbol == 'DOT':
        keywords = ['#DOTUSD', '#DOTUSDT', '#DOT', 'DOT']
    #elif symbol == 'UNI':
    #    keywords = ['#UNIUSD', '#UNIUSDT', '#UNI', 'UNI']
    #elif symbol == 'ICP':
    #    keywords = ['#ICPUSD', '#ICPUSDT', '#ICP', 'ICP']
    elif symbol == 'BCH':
        keywords = ['#BCHUSD', '#BCHUSDT', '#BCH', 'BCH']
    elif symbol == 'LTC':
        keywords = ['#LTCUSD', '#LTCUSDT', '#LTC', 'LTC']
    elif symbol == 'LINK':
        keywords = ['#LINKUSD', '#LINKUSDT', '#LINK', 'LINKUSD']
    elif symbol == 'MATIC':
        keywords = ['#MATICUSD', '#MATICUSDT', '#MATIC', 'MATIC']
    elif symbol == 'SOL':
        keywords = ['#SOLUSD', '#SOLUSDT', '#SOL', 'SOL']
   # elif symbol == 'ETC':
  #      keywords = ['#ETCUSD', '#ETCUSDT', '#ETC', 'ETC']
    #elif symbol == 'XLM':
    #    keywords = ['#XLMUSD', '#XLMUSDT', '#XLM', 'XLM']
    #elif symbol == 'THETA':
    #    keywords = ['#THETAUSD', '#THETAUSDT', '#THETA', 'THETA']
    #elif symbol == 'VET':
    #    keywords = ['#VETUSD', '#VETUSDT', '#VET', 'VET']
    elif symbol == 'EOS':
        keywords = ['#EOSUSD', '#EOSUSDT', '#EOS', 'EOS']
    #elif symbol == 'BNB':
    #    keywords = ['#BNBUSD', '#BNBUSDT', '#BNB', 'BNB']

    return keywords

reddit_blue_print = Blueprint('reddit', __name__)
@reddit_blue_print.route('/reddit', methods=['GET', 'POST'])
@login_required
def run_reddit(start_date=ten_days_ago, end_date=today, **kwargs):
    list = []
    coins = []
    if request.method == 'POST':
        coin_name_1 = request.form['cryptoCoin1']
        coin_name_2 = request.form['cryptoCoin2']
        # #BTC , Bitcoin, #BTCUSDT , BTCUSD
        coin_names = [coin_name_1, coin_name_2]
        for coin in coin_names:
            if coin.strip():  # Skip if coin is an empty string or contains only whitespace
                coins.append(coin)
        historic_data = get_historical_data(coins)
        data_reddit = run_coin_reddit(coins)
        json_obj = {}
        for i, coin in enumerate(data_reddit, start=1):
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
        json_obj['num_of_coins'] = len(data_reddit)
        return render_template('reddit-charts.html', user=current_user, plot_data=json_obj)
    else:
        return render_template('reddit.html')
    

def get_historical_data(symbol_list):
    exchange = ccxt.kraken()
    #exchange = ccxt.binance()
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
    


def run_coin_reddit(list_coin_symbol, start_date=ten_days_ago, end_date=today):
    coins = []
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
        word_json = gen_sent_graph_reddit(word, start_date, end_date)
        word__json_array.append(word_json)
    for json_data in word__json_array:
        json_data = json.loads(json_data)
        x_axis_categories_values[0] += json_data.get("x_axis_categories_values", [])[0]
        x_axis_categories_values[1] += json_data.get("x_axis_categories_values", [])[1]
        x_axis_categories_values[2] += json_data.get("x_axis_categories_values", [])[2]
        

    total = x_axis_categories_values[0] + x_axis_categories_values[1] + x_axis_categories_values[2]
    if total == 0:
        return {'coin name': symbol, 'percentages': [0,0,0], 'x_axis': ['Buy','Sell','Hold'], 'x_axis_categories_values': [0,0,0]}
    else:
        percentages[0] = (x_axis_categories_values[0] / total) * 100
        percentages[1] = (x_axis_categories_values[1] / total) * 100
        percentages[2] = (x_axis_categories_values[2] / total) * 100

        return {'coin name': symbol, 'percentages': percentages, 'x_axis': ['Buy','Sell','Hold'], 'x_axis_categories_values': x_axis_categories_values}





#def run_stock(start_date=ten_days_ago, end_date=today, **kwargs):
    try:
        return gen_sent_graph(kwargs, start_date, end_date)
    except praw.exceptions.APIException as e:
        if e.response.status_code == 503:
            return "The API is temporarily unavailable or experiencing server-side issues. " \
                   "Please try again in a few moments."
    except ZeroDivisionError as e:
        return "There are no results for this search."
    except Exception as e:
        return "An Error has occured, please make sure you've entered the Symbol correctly and with valid dates"

# run_stock(name1="TA-35", name2="TA35", name3="TelAviv-35", start_date="23-07-2022", end_date="26-07-2023")
#
# # ----End Of Cell----
#
# run_stock(name1="BTC-USD", name2="Bitcoin", name3="Bit", start_date="23-07-2022", end_date="26-07-2023")
#
# # ----End Of Cell----
#
# run_stock(name1="SPY", name2="SP&500", name3="SP500", start_date="13-07-2022", end_date="27-07-2023")
#
# # ----End Of Cell----
