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

#from . import db
#from . modules import User


import datetime as DT


# Set up default dates to be fron 90 days ago till today
today = DT.date.today()
two_week_ago = str(today - DT.timedelta(days=90))
today = str(today)

def gen_sent_graph_nasdaq(stock_symbol, start_date,end_date):
    return




def gen_sent_graph_twitter(stock_symbol, start_date, end_date):
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
    search1 = stock_symbol
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

    # Search tweets for tweets mentioning stock symbol
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

    # Calculate stock operations by their weights
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
    percentages = [(sentiment / total) * 100 for sentiment in x_axis_categories_values]
    data = {
    "stock name":stock_symbol,
    "percentages": percentages,
    "x_axis": x_axis,
    "x_axis_categories_values": x_axis_categories_values
    }

    json_data = json.dumps(data)
    #fig, ax = plt.subplots()

    """
    ax.bar(x_axis, percentages, color=['green', 'red', 'blue'], edgecolor='black', linewidth=1, capstyle='round', joinstyle='round')
    # Set y-axis tick labels as percentages
    ax.yaxis.set_major_formatter(mtick.PercentFormatter())
    # Set y-axis tick locator
    ax.yaxis.set_major_locator(mtick.MultipleLocator(base=10))
    # Set y-axis limits
    ax.set_ylim([0, 100])

    plt.title(f'Sentiment around the stock {search1}')
    plt.xlabel('Sentiment')
    plt.ylabel('Positive/Neutral/Negative mentions')
    #plt.show()
    """
    return json_data


def run_stock_twitter(list_stock_symbol, start_date=two_week_ago, end_date=today):
    stocks = []
    for i in range(4):
        stock_data = gen_sent_graph_twitter(list_stock_symbol[i], start_date, end_date)
        #buffer = io.BytesIO()
        #fig.savefig(buffer, format='png')
        #buffer.seek(0)
        #plot_data.append(base64.b64encode(buffer.getvalue()).decode())
        #plt.close(fig)
        stocks.append(stock_data)
    return stocks


def run_stock_nasdaq(list_stock_symbol, start_date=two_week_ago, end_date=today):
    plot_data = []
    api_key = '6P03OIQGX3TR7PH1'
    stocks =[]
    fig, axs = plt.subplots(nrows=len(list_stock_symbol), ncols=1, figsize=(10, 10))
    for i, symbol in enumerate(list_stock_symbol):
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
                
        #axs[i].plot(dates, prices)
       # axs[i].set_title(symbol)
        #axs[i].set_ylabel('Price')
       # axs[i].tick_params(axis='x', rotation=90)
        {"name": symbol,"dates": dates, "prices": prices}
        stocks.append({"name": symbol,"dates": dates, "prices": prices})
    """
    fig.tight_layout()
    buffer = io.BytesIO()
    plt.savefig(buffer, format='png')
    buffer.seek(0)
    image = base64.b64encode(buffer.getvalue()).decode('utf-8')
    plot_data.append(base64.b64encode(buffer.getvalue()).decode())
    #plt.show()
    plt.close(fig)
    """
    return stocks

    #return render_template('stocks.html', image=image)





    



twitter = Blueprint('twitter', __name__)
@twitter.route('/twitter', methods=['GET','POST'])
@login_required
def twitter_nlp():
    list = []
    if request.method == 'POST':
        stock_name_1 = request.form['Stock #1']
        stock_name_2 = request.form['Stock #2']
        stock_name_3 = request.form['Stock #3']
        stock_name_4 = request.form['Stock #4']

        list.append(stock_name_1)
        list.append(stock_name_2)
        list.append(stock_name_3)
        list.append(stock_name_4)

        data_nasdaq = run_stock_nasdaq(list)
        data_twitter = run_stock_twitter(list)
        stock1 =json.loads(data_twitter[0])
        stock2 =json.loads(data_twitter[1])
        stock3 =json.loads(data_twitter[2])
        stock4 =json.loads(data_twitter[3])

        
       # json_array =json.dumps(json_array, indent=4)
       
        json_obj = {
        'stock_name_1': stock1['stock name'],
        'stock_dates_1': data_nasdaq[0]['dates'],
        'stock_prices_1': data_nasdaq[0]['prices'],
        'percentages_1': stock1['percentages'],
        'x_axis_1': stock1['x_axis'],
        'x_axis_categories_values_1': stock1['x_axis_categories_values'],
        'stock_name_2':stock2['stock name'],
        'stock_dates_2': data_nasdaq[1]['dates'],
        'stock_prices_2': data_nasdaq[1]['prices'],
        'percentages_2': stock2['percentages'],
        'x_axis_2': stock2['x_axis'],
        'x_axis_categories_values_2': stock2['x_axis_categories_values'],
        'stock_name_3': stock3['stock name'],
        'stock_dates_3': data_nasdaq[2]['dates'],
        'stock_prices_3': data_nasdaq[2]['prices'],
        'percentages_3': stock3['percentages'],
        'x_axis_3': stock3['x_axis'],
        'x_axis_categories_values_3': stock3['x_axis_categories_values'],
        'stock_name_4':stock4['stock name'],
        'stock_dates_4': data_nasdaq[3]['dates'],
        'stock_prices_4': data_nasdaq[3]['prices'],
        'percentages_4': stock4['percentages'],
        'x_axis_4': stock4['x_axis'],
        'x_axis_categories_values_4': stock4['x_axis_categories_values']

         }
    
        return render_template('charts.html', user=current_user, plot_data=json_obj)                                           
    else:
        return render_template('twitter.html', user=current_user)
    
     #render_template('charts.html', user=current_user, plot_data=json_obj) #jsonify(json_obj) #render_template('charts.html', user=current_user, plot_data=json_array)
@twitter.route('/charts', methods=['GET'])
@login_required
def charts():
    return render_template('charts.html', user=current_user)