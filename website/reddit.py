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
import base64


def gen_sent_graph(stock_symbol, start_date, end_date):
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
    date_format = '%d-%m-%Y'
    start_date = datetime.strptime(start_date, date_format)
    end_date = datetime.strptime(end_date, date_format)

    # Get all stock name variations
    names = list(stock_symbol.values())

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
    sum_upvotes = p_buy + p_sell + p_hold

    buy_p = round((p_buy), 2)
    sell_p = round((p_sell), 2)
    hold_p = round((p_hold), 2)

    # Check if there are any sentiment scores
    if sum_upvotes == 0:
        # No sentiment scores, add a message and return
        return {
            'graph': None,
            'symbol': stock_symbol,
            'message': 'No sentiment data available for the given date range.'
        }

    # Data for the pie chart
    labels = ['Buy', 'Sell', 'Hold']
    sizes = [buy_p, sell_p, hold_p]  # Values corresponding to each label

    # Create the pie chart
    plt.pie(sizes, labels=labels, autopct='%1.1f%%')

    # Add a title
    plt.title(f'Sentiment percentage around the stock {names[0]}')

    # Save the chart to a buffer
    buffer = io.BytesIO()
    plt.savefig(buffer, format='png')
    buffer.seek(0)

    # Convert the buffer content to a base64-encoded string
    graph_base64 = base64.b64encode(buffer.read()).decode()

    # Close the buffer and clear the plot
    buffer.close()
    plt.close()

    # Return the base64-encoded graph and symbol
    return {
        'graph': graph_base64,
        'symbol': stock_symbol
    }


# Set up default dates to be from 90 days ago till today
today = datetime.now()
two_weeks_ago = today - DT.timedelta(weeks=14)

today = datetime.strftime(today, '%d-%m-%Y')
two_weeks_ago = datetime.strftime(two_weeks_ago, '%d-%m-%Y')

reddit_blue_print = Blueprint('reddit', __name__)


@reddit_blue_print.route('/reddit', methods=['GET', 'POST'])
@login_required
def run_reddit(start_date=two_weeks_ago, end_date=today, **kwargs):
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
        data_reddit = run_coin_reddit(coins)
        return render_template('reddit-charts.html', user=current_user, plot_data=data_reddit)
    else:
        return render_template('reddit.html')


def run_coin_reddit(list_coin_symbol, start_date=two_weeks_ago, end_date=today):
    res_data = []
    for symbol in list_coin_symbol:
        coin_data = run_stock(my_symbol=symbol)
        res_data.append(coin_data)
    return res_data


def run_stock(start_date=two_weeks_ago, end_date=today, **kwargs):
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
