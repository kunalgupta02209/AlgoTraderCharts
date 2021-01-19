# app.py
from types import TracebackType
from flask import Flask, request, jsonify, render_template
import json
import pytz
import pymongo
from bson.codec_options import CodecOptions
from chart_server.static.config import config as cfg
from chart_server.db.util import log, CLIENT, TIMEZONE, get_ohlc, OHLCInterval, get_ticks
from chart_server.db.constants import TransactionType
import pandas as pd
import re
from datetime import datetime as dt
from datetime import timedelta
import talib
import numpy as np






chart_server = Flask(__name__)

minute_db = CLIENT['NSE_DB_MINUTE'].with_options(codec_options=CodecOptions(tz_aware=True, tzinfo=TIMEZONE),read_concern=pymongo.read_concern.ReadConcern('local'))
symbols_list = list(minute_db.list_collection_names())

chart_server.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
backtest_file_name = ""

def getApp():
	return chart_server


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
def get_formatted_ohlc(
		backtest_stock=None,backtest_interval=OHLCInterval.Minute_1,
		backtest_start_date=None,backtest_end_date=None,
		backtest_buy_signals_list=None,backtest_sell_signals_list=None):
	if backtest_stock is not None:
		stock_name = backtest_stock
		interval = backtest_interval
		start_date = dt.strptime(backtest_start_date,"%Y-%m-%d %H:%M:%S") - timedelta(days=3)
		end_date =  dt.strptime(backtest_end_date,"%Y-%m-%d %H:%M:%S") + timedelta(days=5)
	elif request.method == 'POST':
		stock_name = request.form.get('stock-name')
		interval = request.form.get('select-interval')
		start_date = dt.strptime(request.form.get('start-date'),"%Y-%m-%d").replace(hour=9,minute=15,second=0,microsecond=0)
		end_date = dt.strptime(request.form.get('end-date'),"%Y-%m-%d").replace(hour=15,minute=30,second=0,microsecond=0)
	else:
		stock_name = 'HDFCBANK'
		interval = OHLCInterval.Minute_1
		start_date = (dt.now()-timedelta(days=14)).replace(hour=9,minute=15,second=0,microsecond=0)
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
		try:
			new_df['volume'] = df.volume
		except:
			new_df['volume'] = 0
		df = new_df
		df['timestamp'] = df['timestamp'].astype(dtype='string')
		df_json = df.to_numpy().tolist()
	else:
		df = get_ohlc(stock_name,interval=interval,from_d=start_date, to_d=end_date)
		upper, middle, lower = talib.BBANDS(df['close'],timeperiod=20)
		# df['upper'] = upper
		# df['lower'] = lower
		# df['middle'] = middle
		bb_m = ((upper-middle)/middle)*100
		bb_m_max = np.max(bb_m)
		df['bb_m'] = bb_m/bb_m_max
		df['bbw'] = (upper-lower)/middle
		df.dropna(inplace=True)
		df.reset_index(drop=True,inplace=True)
		if 'oi' in df.keys():
			df = df.drop('oi',axis=1)
		df['timestamp'] = df['timestamp'].astype(dtype='string')
		# log.info(df)
		df_json = df.to_numpy().tolist()
	error_text = ""
	buy_signals_list = []
	sell_signals_list = []
	if backtest_buy_signals_list is not None:
		buy_signals_list = backtest_buy_signals_list
	if backtest_sell_signals_list is not None:
		sell_signals_list = backtest_sell_signals_list
	data = {
		"stock-name":stock_name,
		"error-text":error_text,
		"ohlc":df_json,
		"buy-list":buy_signals_list,
		"sell-list":sell_signals_list,
	}
	# log.info(df_json)
	return jsonify(data)

@chart_server.route('/extract_trading_symbols',methods=['POST'])
def extract_trading_symbols():
	global backtest_file_name
	file_path = request.form.get('backtest-file-input')
	with open('backtest_file_name.txt') as f:
		backtest_file_name = f.readline()
	if file_path is not None and file_path != "":
		backtest_file_name = file_path
	# log.info(backtest_file_name)
	df = pd.read_csv(backtest_file_name,names=['timestamp','tradingsymbol'
												,'entry_exit','buy_sell'
												,'qty','price','pnl','arg1'])
	# df = pd.read_csv(backtest_file_name)
	trading_symbols = []
	for symbol in list(df['tradingsymbol']):
		if symbol not in trading_symbols:
			trading_symbols.append(symbol)
	return jsonify(trading_symbols)
	


@chart_server.route('/read-backtest',methods=['POST'])
def read_backtest():
	global backtest_file_name
	tradingsymbol = request.form.get('tradingsymbol')
	file_path = request.form.get('backtest-file-input')
	interval = request.form.get('interval')
	with open('backtest_file_name.txt') as f:
		backtest_file_name = f.readline()
	if file_path is not None and file_path != "":
		backtest_file_name = file_path
	df = pd.read_csv(backtest_file_name,names=['timestamp','tradingsymbol'
												,'entry_exit','buy_sell'
												,'qty','price','pnl','arg1'])
	# df = pd.read_csv(backtest_file_name)
	df = df[df['tradingsymbol'] == tradingsymbol]
	print(df)
	df_buy = df[df['buy_sell'] == "TransactionType.Buy"]
	df_sell = df[df['buy_sell'] == "TransactionType.Sell"]
	buy_list = list(df_buy['timestamp'])
	sell_list = list(df_sell['timestamp'])
	start_time = df.timestamp.iloc[0]
	end_time = df.timestamp.iloc[-1]
	
	return get_formatted_ohlc(backtest_stock=tradingsymbol,backtest_interval=interval,
						backtest_start_date=start_time,
						backtest_end_date=end_time,
						backtest_buy_signals_list=buy_list,
						backtest_sell_signals_list=sell_list)
	



# A welcome message to test our server
@chart_server.route('/')
def index():
	return render_template("index.html",interval_list=OHLCInterval.interval_list)

if __name__ == '__main__':
	# Threaded option to enable multiple instances for multiple user access support
	chart_server.run(threaded=True, port=5000)