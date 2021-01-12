# app.py
from flask import Flask, request, jsonify, render_template
import json
import pytz
import pymongo
from bson.codec_options import CodecOptions
from chart_server.static.config import config as cfg
from chart_server.db.util import log, CLIENT, TIMEZONE, get_ohlc, OHLCInterval
import pandas as pd
import re






chart_server = Flask(__name__)

minute_db = CLIENT['NSE_DB_MINUTE'].with_options(codec_options=CodecOptions(tz_aware=True, tzinfo=TIMEZONE),read_concern=pymongo.read_concern.ReadConcern('local'))
symbols_list = list(minute_db.list_collection_names())

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
    # log.info(data)
    return jsonify(data)

@chart_server.route('/getOHLC')
def get_formatted_ohlc():
    df = get_ohlc('HDFC',OHLCInterval.Minute_1)
    df.reset_index(drop=True,inplace=True)
    df = df.drop('oi',axis=1)
    # df['timestamp'] = df['timestamp'].apply(lambda x: f'"{x}"')
    df['timestamp'] = df['timestamp'].astype(dtype='string')
    # log.info(df)
    df_json = df.to_numpy().tolist()
    # log.info(df_json)
    import datetime
    date_handler = lambda obj: (
            obj.isoformat()
            if isinstance(obj, (datetime.datetime, datetime.date, pd.Timestamp))
            else None
        )
    # df_json = json.dumps(df_json,default=date_handler)
    # log.info(json.dumps(df_json))
    # log.info(df_json)
    return jsonify(df_json)


# A welcome message to test our server
@chart_server.route('/')
def index():
    return render_template("index.html",interval_list=OHLCInterval.interval_list)

if __name__ == '__main__':
    # Threaded option to enable multiple instances for multiple user access support
    chart_server.run(threaded=True, port=5000)