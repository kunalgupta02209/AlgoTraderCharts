# app.py
from flask import Flask, request, jsonify, render_template
import json
import pytz
import pymongo
from bson.codec_options import CodecOptions
from chart_server.static.config import config as cfg
from chart_server.db.util import log, CLIENT, TIMEZONE, get_ohlc, OHLCInterval, get_ticks
import pandas as pd
import re
from datetime import datetime as dt
from datetime import timedelta






chart_server = Flask(__name__)

minute_db = CLIENT['NSE_DB_MINUTE'].with_options(codec_options=CodecOptions(tz_aware=True, tzinfo=TIMEZONE),read_concern=pymongo.read_concern.ReadConcern('local'))
symbols_list = list(minute_db.list_collection_names())

chart_server.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0

def getApp():
    return chart_server
@chart_server.route('/update_list', methods = ['POST'])
def update_list():
    
    return render_template("scores.html")

@chart_server.route('/show_scores')
def show_scores():
    return render_template("scores.html")

@chart_server.route('/autocomplete', methods = ['GET'])
def get_stock_list():
    search_name = request.args.get('term')
    if isinstance(search_name,str):
        search_name = search_name.upper()
    else:
        return jsonify([])
    data = [stock for stock in symbols_list if re.search(search_name,stock)]
    data = data[:10]
    # log.info(data)
    return jsonify(data)

@chart_server.route('/getOHLC', methods= ['GET','POST'])
def get_formatted_ohlc():
    if request.method == 'POST':
        stock_name = request.form.get('stock-name')
        interval = request.form.get('select-interval')
        start_date = dt.strptime(request.form.get('start-date'),"%Y-%m-%d").replace(hour=9,minute=15,second=0,microsecond=0)
        end_date = dt.strptime(request.form.get('end-date'),"%Y-%m-%d").replace(hour=15,minute=30,second=0,microsecond=0)
    else:
        stock_name = 'HDFCBANK'
        interval = OHLCInterval.Minute_1
        start_date = (dt.now()-timedelta(days=7)).replace(hour=9,minute=15,second=0,microsecond=0)
        end_date = dt.now()
    if interval == OHLCInterval.Tick:
        df = get_ticks(stock_name,from_d=start_date, to_d=end_date)
        df.reset_index(drop=False,inplace=True)
        new_df = pd.DataFrame()
        new_df['timestamp'] = df.timestamp
        new_df['open'] = df.last_price
        new_df['high'] = df.last_price
        new_df['low'] = df.last_price
        new_df['close'] = df.last_price
        new_df['volume'] = df.volume
        df = new_df
        df['timestamp'] = df['timestamp'].astype(dtype='string')
        df_json = df.to_numpy().tolist()
    else:
        df = get_ohlc(stock_name,interval=interval,from_d=start_date, to_d=end_date)
        df.reset_index(drop=True,inplace=True)
        df = df.drop('oi',axis=1)
        df['timestamp'] = df['timestamp'].astype(dtype='string')
        # log.info(df)
        df_json = df.to_numpy().tolist()
    error_text = ""
    buy_signals_list = []
    sell_signals_list = []
    data = {
        "stock-name":stock_name,
        "error-text":error_text,
        "ohlc":df_json,
        "buy-signals":buy_signals_list,
        "sell-signals":sell_signals_list,
    }
    # log.info(df_json)
    return jsonify(data)


# A welcome message to test our server
@chart_server.route('/')
def index():
    return render_template("index.html",interval_list=OHLCInterval.interval_list)

if __name__ == '__main__':
    # Threaded option to enable multiple instances for multiple user access support
    chart_server.run(threaded=True, port=5000)