import pytz
import pymongo
from bson.codec_options import CodecOptions
from chart_server.static.config import config as cfg
import logging
from chart_server.db.constants import OHLCInterval,DB_NAMES,ResampleInterval
from datetime import datetime as dt
from datetime import timedelta
import pandas as pd
from pandas.tseries.frequencies import to_offset

log = logging.getLogger('root')
c_handler = logging.StreamHandler()
c_handler.setLevel(logging.DEBUG)
c_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')      
c_handler.setFormatter(c_format)
log.addHandler(c_handler)
log.setLevel(logging.DEBUG)

TIMEZONE = pytz.timezone(cfg.timezone)
CLIENT = pymongo.MongoClient(cfg.mongodb_url)
log.debug(CLIENT.server_info())

def _get_ohlc(symbol, interval = OHLCInterval.Minute_1, 
		from_d = dt.now() - timedelta(days=5), to_d = dt.now()):
	if from_d.tzinfo is None:
		from_d = TIMEZONE.localize(from_d)
		to_d = TIMEZONE.localize(to_d)
	
	collection = CLIENT[DB_NAMES[interval]][symbol].with_options(
			codec_options=CodecOptions(tz_aware=True, tzinfo=TIMEZONE))
	result = collection.find({'_id.timestamp':{
					'$gte':from_d,
					'$lt':to_d
					}})
	df = pd.DataFrame(data=list(result))
	try:
		df['timestamp'] = df['_id'].apply(lambda x: x['timestamp'])
	except:
		return pd.DataFrame(columns=['timestamp','open','high','low','close','volume'])
	df.set_index('timestamp', drop=True, inplace=True)
	df.drop('_id', axis = 1, inplace = True)
	return df

def get_ohlc(symbol, interval = OHLCInterval.Minute_1,
		from_d = dt.now() - timedelta(days=5), to_d = dt.now(), to_csv = False):
	if from_d.tzinfo is None:
		from_d = TIMEZONE.localize(from_d)
		to_d = TIMEZONE.localize(to_d)
	final_df = None
	if OHLCInterval.Day_1 != interval and OHLCInterval.Minute_1 != interval and OHLCInterval.Minute_60 != interval:
		if OHLCInterval.Month_1 == interval or OHLCInterval.Week_1 == interval:
			df = _get_ohlc(symbol, OHLCInterval.Day_1, from_d, to_d)
		elif OHLCInterval.Hour_2 == interval or OHLCInterval.Hour_3 == interval or OHLCInterval.Hour_4 == interval:
			df = _get_ohlc(symbol, OHLCInterval.Minute_60, from_d, to_d)
		else:
			df = _get_ohlc(symbol, OHLCInterval.Minute_1, from_d, to_d)
		if len(df) == 0:
			return df
		df_ = pd.DataFrame()
		interval, offset = ResampleInterval[interval]
		if offset != 0:
			df.index = df.index - to_offset(timedelta(minutes=offset))
		df_['open'] = df['open'].resample(interval).first()
		df_['high'] = df['high'].resample(interval).max()
		df_['low'] = df['low'].resample(interval).min()
		df_['close'] = df['close'].resample(interval).last()
		df_['volume'] = df['volume'].resample(interval).sum()
		df_['oi'] = df['oi'].resample(interval).last()
		df_.dropna(inplace=True)
		if offset != 0:
			df_.index = df_.index + to_offset(timedelta(minutes=offset))
		final_df = df_
	else:
		df = _get_ohlc(symbol, interval, from_d, to_d)
		if len(df) == 0:
			return df
		final_df = df
	final_df.reset_index(inplace=True)
	final_df['timestamp'] = final_df['timestamp'].dt.tz_localize(None)
	final_df.set_index('timestamp',drop=False,inplace=True)
	final_df.sort_index(inplace=True)
	if to_csv == True:
		final_df.to_csv(symbol+"_"+interval+"_"+str(to_d.strftime("%Y-%m-%d")+".csv"))
	return final_df

def get_ticks(symbol,from_d = dt.now() - timedelta(days=5),
		to_d = dt.now(), backtest = False, ret_dict = False):
	if from_d.tzinfo is None:
		from_d = TIMEZONE.localize(from_d)
		to_d = TIMEZONE.localize(to_d)
	collection = CLIENT[DB_NAMES['tick']][symbol].with_options(codec_options=CodecOptions(tz_aware=True, tzinfo=TIMEZONE),read_concern=pymongo.read_concern.ReadConcern('local'))	
	if backtest or ret_dict:
		result = collection.find({'_id.timestamp':{
					'$gte':from_d,
					'$lte':to_d
					}},{"_id":1,"last_price":1,"instrument_token":1}).sort("_id",direction=pymongo.ASCENDING)
		if ret_dict:
			return list(result)
		df = pd.DataFrame(columns=['timestamp',symbol])
		df[symbol] = list(result)
		if len(df) == 0:
			return df
		df['timestamp'] = df[symbol].apply(lambda x: x['_id']['timestamp'].replace(tzinfo=None))
		df.set_index('timestamp', inplace=True)
		return df
	result = collection.find({'_id.timestamp':{
					'$gte':from_d,
					'$lte':to_d
					}},{"_id":1,"last_price":1,"volume":1,"oi":1}).sort("_id",direction=pymongo.ASCENDING)
	df = pd.DataFrame(data=list(result))
	if len(df) == 0:
		return df
	df['timestamp'] = df['_id'].apply(lambda x: x['timestamp'].replace(tzinfo=None))
	df.set_index('timestamp', drop=True, inplace=True)
	df.drop('_id', axis = 1, inplace = True)
	return df