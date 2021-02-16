import pandas as pd
import numpy as np
import talib
from sortedcontainers import SortedDict
import warnings
def CDLHAMMER(open, high, low, close):
	result = (((high - low)>3*(open -close)) &  
			((close - low)/(0.001 + high - low) > 0.6) & 
			((open - low)/(0.001 + high - low) > 0.6))
	result = result.apply(lambda x: 100 if x else 0)
	return result

def CDLENGULFING(open, high, low, close):
	result_bull = ((open.shift(1) > close.shift(1)) & (close > open )
		& (close >= open.shift(1)) & (close.shift(1) >= open )
		& (close - open > open.shift(1) - close.shift(1)) )
	result_bear = ((close.shift(1) > open.shift(1)) & (open > close )
		& (open >= close.shift(1)) & (open.shift(1) >= close )
		& (open - close > close.shift(1) - open.shift(1) ) )
	result_bull = result_bull.apply(lambda x: 100 if x else 0)
	result_bear = result_bear.apply(lambda x: -100 if x else 0)
	result = result_bull + result_bear
	return result

def CDLSHOOTINGSTAR(open, high, low, close):
	result = ((open.shift(1) < close.shift(1)) & (open > close.shift(1)) 
		& ((high - np.maximum(open, close)) >= ((open - close).abs() * 3 ))
		& ((np.minimum(close, open) - low) <= ((high - np.maximum(open, close))*3)) )
	result = result.apply(lambda x: -100 if x else 0)
	return result
	
def CDLDARKCLOUDCOVER(open, high, low, close):
	result = ((close.shift(1)>open.shift(1)) & (((close.shift(1)+open.shift(1))/2)>close)
		& (open>close) & (open>close.shift(1)) & (close>open.shift(1)) 
		& ((open-close)/(0.001+(high-low)) > 0.6))
	result = result.apply(lambda x: -100 if x else 0)
	return result
	
def CDLEVENINGSTAR(open, high, low, close):
	result = ( (close.shift(-2) > open.shift(-2) )
		& (np.minimum(open.shift(1), close.shift(1)) > close.shift(-2) )
		& (open < np.minimum(open.shift(1), close.shift(1))) 
		& (close < open ) )
	result = result.apply(lambda x: -100 if x else 0)
	return result

def CDLHARAMI(open, high, low, close):
	result_bull = ((open.shift(1) > close.shift(1)) 
		& (close > open) & (close <= open.shift(1) )
		& (close.shift(1) <= open )
		& (close - open) < (open.shift(1) - close.shift(1)) )
	result_bear = ((close.shift(1) > open.shift(1) )
		& (open > close) & (open <= close.shift(1)) 
		& (open.shift(1) <= close) 
		& ((open - close) < (close.shift(1) - open.shift(1))) )
	result_bull = result_bull.apply(lambda x: 100 if x else 0)
	result_bear = result_bear.apply(lambda x: -100 if x else 0)
	result = result_bull + result_bear
	return result

def CDLPIERCING(open, high, low, close):
	result = ((close.shift(1) < open.shift(1) )
		& (open < low.shift(1)) 
		& (close > (close.shift(1) + ((open.shift(1) - close.shift(1))/2)) )
		& (close < open.shift(1)))
	result = result.apply(lambda x: 100 if x else 0)
	return result

def CDLSPINNINGTOP(open, high, low, close):
	return talib.CDLSPINNINGTOP(open,high,low,close)

def CCI(high,low,close, timeperiod): 
	TP = (high + low + close) / 3 
	CCI = pd.Series((TP - TP.rolling(timeperiod).mean()) / (0.015 * TP.rolling(timeperiod).std()),
					name = 'CCI') 
	# data = data.join(CCI) 
	return CCI

def TMA(open,high,low,close,atr=2,multiplier=1,cci=10):
	"""Trend Moving Averaage
	"""
	df = pd.DataFrame()
	df['tr'] = talib.TRANGE(high,low,close)
	df['wma'] = talib.WMA(df.tr,timeperiod=atr)
	df['CCI'] = talib.CCI(close,close,close,timeperiod=cci)
	df['bufferDn'] = pd.Series(high + multiplier * df.wma)
	df['bufferUp'] = pd.Series(low - multiplier * df.wma)
	df.reset_index(inplace=True,drop=True)
	df.fillna( value=0,inplace=True)
	for i,v in df.iterrows():
		if i == 0:
			continue
		if df.at[i,'CCI'] >= 0 and df.at[i-1, 'CCI'] < 0:
			df.at[i,'bufferUp'] = df.at[i-1,'bufferDn']
		if df.at[i,'CCI'] <= 0 and df.at[i-1,'CCI'] > 0:
			df.at[i,'bufferDn'] = df.at[i-1,'bufferUp']
		if df.at[i,'CCI'] >= 0:
			if (df.at[i,'bufferUp'] < df.at[i-1,'bufferUp']):
				df.at[i,'bufferUp'] = df.at[i-1,'bufferUp']
		else:
			if df.at[i,'CCI'] <= 0:
				if df.at[i,'bufferDn'] > df.at[i-1,'bufferDn']:
					df.at[i,'bufferDn'] = df.at[i-1,'bufferDn']

	df['x'] = np.where(df.CCI >= 0, df.bufferUp, df.bufferDn)
	for i,v in df.iterrows():
		if i == 0:
			df.at[0,'color'] = 100
			continue
		df.at[i,'color'] = 100 if df.at[i,'x'] > df.at[i-1,'x'] else -100 if df.at[i,'x'] < df.at[i-1,'x'] else df.at[i-1,'color']
	for i,v in df.iterrows():
		if i == 0:
			df.at[0,'ind'] = 100
			continue
		df.at[i,'ind'] = 100 if df.at[i,'color'] > df.at[i-1,'color'] else -100 if df.at[i,'color'] < df.at[i-1,'color'] else 0
	return df.ind.values,df.color.values

def dzsz(open,high,low,close,
		min_legin=1,min_legout=2,min_base=1,
		max_legin=2,max_legout=6,max_base=6,
		demand_dict = None,
		supply_dict = None,
		use_proximal = False):
	ind_arr = open.index.array
	def body_range(ind):
		cdl_range = high.iloc[ind] - low.iloc[ind]
		cdl_body = abs(close.iloc[ind] - open.iloc[ind])
		# cdl_body = 0.05 if cdl_body == 0 else cdl_body
		cdl_body,cdl_range = (0.0,1) if cdl_range == 0 else (cdl_body,cdl_range)
		#Debugging cdl_body,cdl_range runtime warning 
		# with warnings.catch_warnings(record=True) as w:
		#     # Cause all warnings to always be triggered.
		#     warnings.simplefilter("always")
		#     # Trigger a warning.
		#     cdl_body_range = cdl_body/cdl_range
		#     if len(w) != 0:
		#         print(cdl_range,cdl_body_range,cdl_body)
		# print(f"{ind_arr[ind]}\t CDLRANGE\t {cdl_body_range}",end='\t')
		cdl_body_range = cdl_body/cdl_range
		return cdl_body_range
	def green(ind):
		return (close.iloc[ind] > open.iloc[ind]) and (body_range(ind) > 0.55)
	def red(ind):
		return (close.iloc[ind] < open.iloc[ind]) and (body_range(ind) > 0.55)

	def rally(ind, leg_size):
		leg = True
		for i in range(ind, ind-leg_size+1,-1):
			if green(i):
				pass
			else:
				leg = False
		if leg:
			if green(ind-leg_size+1):
				return leg
			else:
				if body_range(ind-leg_size+1) < 0.5 and low[ind-leg_size+1] > high[ind-leg_size]:
					return leg
				else:
					return False
		return leg
	def drop(ind, leg_size):
		leg = True
		for i in range(ind, ind-leg_size+1,-1):
			if red(i):
				pass
			else:
				leg = False
		if leg:
			if red(ind-leg_size+1):
				return leg
			else:
				if body_range(ind-leg_size+1) < 0.5 and high[ind-leg_size+1] < low[ind-leg_size]:
					return leg
				else:
					return False
		return leg
	
	def legout(ind, leg_length = min_legout): 
		is_rally = rally(ind, leg_length)
		is_drop = drop(ind, leg_length)
		if is_rally:
			return {'distal':low.iloc[ind],'is_rally':True}
		if is_drop:
			return {'distal':high.iloc[ind],'is_rally':False}
		return {'distal':False,'is_rally':None}
	
	def base(base_start, base_length = min_base, is_rally=True):
		is_base = True
		proximal = 0 if is_rally else 99999999
		distal = 99999999 if is_rally else 0
		for i in range(base_start,base_start-base_length,-1):
			if body_range(i) <=0.5:
				proximal = max(proximal,close.iloc[i],open.iloc[i]) if is_rally else min(proximal,close.iloc[i],open.iloc[i])
				distal = min(distal,low.iloc[i]) if is_rally else max(distal,high.iloc[i])
			else:
				is_base = False
				break
		if is_base:
			if is_rally:
				is_base = proximal < close.iloc[base_start+1]
			else:
				is_base = proximal > close.iloc[base_start+1]
		return {'is_base':is_base,'proximal':proximal,'distal':distal}
	
	def legin(ind, legin_length = min_legin):
		is_rally = rally(ind, legin_length)
		is_drop = drop(ind, legin_length)
		if is_rally:
			return {'distal':high.iloc[ind],'is_rally':True}
		if is_drop:
			return {'distal':low.iloc[ind],'is_rally':False}
		return {'distal':False,'is_rally':None}

	demand_dict = SortedDict() if demand_dict is None else demand_dict
	supply_dict = SortedDict() if supply_dict is None else supply_dict
	ind_list = []
	if use_proximal:
		for ind in range(-len(open)+15,-1):
			# check for legout length
			for i in range(max_legout,min_legout-1,-1):
				is_legout = legout(ind, i)
				if is_legout['distal']:
					for j in range(max_base, min_base-1, -1):
						is_base = base(ind-i,j,is_legout['is_rally'])
						if is_base['is_base']:
							for k in range(max_legin,min_legin-1,-1):
								is_legin = legin(ind-i-j,k)
								if is_legin['distal']:
									ind_list.append(ind)
									if is_legout['is_rally']: #_brally
										proximal = is_base['proximal']
										distal = min(is_base['distal'],is_legout['distal']) if is_legin['is_rally'] else min(is_base['distal'],is_legin['distal'],is_legout['distal'])
										if proximal not in demand_dict.keys():                                        
											demand_dict.update({proximal:{"timestamp":ind_arr[ind],
																				"legout_length":i,"base_length":j,"legin_length":k,
																				"proximal":proximal,"distal":distal}})
									else: #_bdrop
										proximal = is_base['proximal']
										distal = max(is_base['distal'],is_legout['distal']) if not is_legin['is_rally'] else max(is_base['distal'],is_legin['distal'],is_legout['distal'])
										if proximal not in supply_dict.keys():
											supply_dict.update({proximal:{"timestamp":ind_arr[ind],
																				"legout_length":i,"base_length":j,"legin_length":k,
																				"proximal":proximal,"distal":distal}})
			# Elimination method 1
			if len(demand_dict.keys()) != 0:
				# print(list(demand_dict.keys()), low[ind])
				while low[ind] < demand_dict.keys()[-1]:
					demand_dict.popitem(index = -1)
					if len(demand_dict.keys()) == 0:
						break
			if len(supply_dict.keys()) != 0:
				# print(list(demand_dict.keys()), low[ind])
				while high[ind] > supply_dict.keys()[0]:
					supply_dict.popitem(index = 0)
					if len(supply_dict.keys()) == 0:
						break
	else:
		for ind in range(-len(open)+15,-1):
			# check for legout length
			for i in range(max_legout,min_legout-1,-1):
				is_legout = legout(ind, i)
				if is_legout['distal']:
					for j in range(max_base, min_base-1, -1):
						is_base = base(ind-i,j,is_legout['is_rally'])
						if is_base['is_base']:
							for k in range(max_legin,min_legin-1,-1):
								is_legin = legin(ind-i-j,k)
								if is_legin['distal']:
									ind_list.append(ind)
									if is_legout['is_rally']: #_brally
										proximal = is_base['proximal']
										distal = min(is_base['distal'],is_legout['distal']) if is_legin['is_rally'] else min(is_base['distal'],is_legin['distal'],is_legout['distal'])
										if distal not in demand_dict.keys():                                        
											demand_dict.update({distal:{"timestamp":ind_arr[ind],
																				"legout_length":i,"base_length":j,"legin_length":k,
																				"proximal":proximal,"distal":distal}})
									else: #_bdrop
										proximal = is_base['proximal']
										distal = max(is_base['distal'],is_legout['distal']) if not is_legin['is_rally'] else max(is_base['distal'],is_legin['distal'],is_legout['distal'])
										if distal not in supply_dict.keys():
											supply_dict.update({distal:{"timestamp":ind_arr[ind],
																				"legout_length":i,"base_length":j,"legin_length":k,
																				"proximal":proximal,"distal":distal}})
			# Elimination method 1
			if len(demand_dict.keys()) != 0:
				while close[ind] < demand_dict.keys()[-1]:
					demand_dict.popitem(index = -1)
					if len(demand_dict.keys()) == 0:
						break
			if len(supply_dict.keys()) != 0:
				while close[ind] > supply_dict.keys()[0]:
					supply_dict.popitem(index = 0)
					if len(supply_dict.keys()) == 0:
						break
						
	df_demand = pd.DataFrame(demand_dict.values(),index = demand_dict.keys())
	df_supply = pd.DataFrame(supply_dict.values(),index = supply_dict.keys())
	
	return (df_demand,df_supply,demand_dict,supply_dict)


def SuperTrend(high, low, close, timeperiod = 10, multiplier = 3):
	"""
	Function to compute SuperTrend
	
	Args :
		df : Pandas DataFrame which contains ['date', 'open', 'high', 'low', 'close', 'volume'] columns
		period : Integer indicates the period of computation in terms of number of candles
		multiplier : Integer indicates value to multiply the ATR
		ohlc: List defining OHLC Column names (default ['Open', 'High', 'Low', 'Close'])
		
	Returns :
		SuperTrend : indicator Series
		SuperTrendX : Direction Series
		SuperTrendSignal : Buy or Sell Signal
	"""
	df = pd.DataFrame()
	df['high'] = high
	df['low'] = low
	df['close'] = close
	atr = 'ATR_' + str(timeperiod)
	st = 'ST_' + str(timeperiod) + '_' + str(multiplier)
	stx = 'STX_' + str(timeperiod) + '_' + str(multiplier)
	sts = 'STS_' + str(timeperiod) + '_' + str(multiplier)
	df[atr] = talib.ATR(high, low, close, timeperiod = timeperiod)
	"""
	SuperTrend Algorithm :
	
		BASIC UPPERBAND = (HIGH + LOW) / 2 + Multiplier * ATR
		BASIC LOWERBAND = (HIGH + LOW) / 2 - Multiplier * ATR
		
		FINAL UPPERBAND = IF( (Current BASICUPPERBAND < Previous FINAL UPPERBAND) or (Previous Close > Previous FINAL UPPERBAND))
							THEN (Current BASIC UPPERBAND) ELSE Previous FINALUPPERBAND)
		FINAL LOWERBAND = IF( (Current BASIC LOWERBAND > Previous FINAL LOWERBAND) or (Previous Close < Previous FINAL LOWERBAND)) 
							THEN (Current BASIC LOWERBAND) ELSE Previous FINAL LOWERBAND)
		
		SUPERTREND = IF((Previous SUPERTREND = Previous FINAL UPPERBAND) and (Current Close <= Current FINAL UPPERBAND)) THEN
						Current FINAL UPPERBAND
					ELSE
						IF((Previous SUPERTREND = Previous FINAL UPPERBAND) and (Current Close > Current FINAL UPPERBAND)) THEN
							Current FINAL LOWERBAND
						ELSE
							IF((Previous SUPERTREND = Previous FINAL LOWERBAND) and (Current Close >= Current FINAL LOWERBAND)) THEN
								Current FINAL LOWERBAND
							ELSE
								IF((Previous SUPERTREND = Previous FINAL LOWERBAND) and (Current Close < Current FINAL LOWERBAND)) THEN
									Current FINAL UPPERBAND
	"""
	
	# Compute basic upper and lower bands
	df['basic_ub'] = (df.high + df.low) / 2 + multiplier * df[atr]
	df['basic_lb'] = (df.high + df.low) / 2 - multiplier * df[atr]

	# Compute final upper and lower bands
	df['final_ub'] = 0.00
	df['final_lb'] = 0.00
	for i in range(timeperiod, len(df)):
		df['final_ub'].iat[i] = df['basic_ub'].iat[i] if df['basic_ub'].iat[i] < df['final_ub'].iat[i - 1] or df.close.iat[i - 1] > df['final_ub'].iat[i - 1] else df['final_ub'].iat[i - 1]
		df['final_lb'].iat[i] = df['basic_lb'].iat[i] if df['basic_lb'].iat[i] > df['final_lb'].iat[i - 1] or df.close.iat[i - 1] < df['final_lb'].iat[i - 1] else df['final_lb'].iat[i - 1]
	   
	# Set the Supertrend value
	df[st] = 0.00
	for i in range(timeperiod, len(df)):
		df[st].iat[i] = df['final_ub'].iat[i] if df[st].iat[i - 1] == df['final_ub'].iat[i - 1] and df.close.iat[i] <= df['final_ub'].iat[i] else \
						df['final_lb'].iat[i] if df[st].iat[i - 1] == df['final_ub'].iat[i - 1] and df.close.iat[i] >  df['final_ub'].iat[i] else \
						df['final_lb'].iat[i] if df[st].iat[i - 1] == df['final_lb'].iat[i - 1] and df.close.iat[i] >= df['final_lb'].iat[i] else \
						df['final_ub'].iat[i] if df[st].iat[i - 1] == df['final_lb'].iat[i - 1] and df.close.iat[i] <  df['final_lb'].iat[i] else 0.00 
				 
	# Mark the trend direction up/down
	df[stx] = np.where((df[st] > 0.00), np.where((df.close < df[st]), -1,  1), np.NaN)
	df[sts] = np.where((df[stx] > df[stx].shift(1)), 1,np.where((df[stx] < df[stx].shift(1)),-1, 0))
	# Remove basic and final bands from the columns
	df.drop(['basic_ub', 'basic_lb', 'final_ub', 'final_lb'], inplace=True, axis=1)
	
	df.fillna(0, inplace=True)

	return (df[st],df[stx],df[sts])

def alert_candle(open,high,low,close):
	hammer = CDLHAMMER(open,high,low,close)
	df = pd.DataFrame(hammer)
	alert_hammer = np.where((close.shift(1) < low.shift(2)) &
		(close > high.shift(1)) &
		(hammer != 0),100,0)
	alert_high = np.where((close.shift(2) < low.shift(3)) & 
		(close.shift(1) > high.shift(2)) &
		(high > high.shift(1)), 200, 0)
	
	df['alert'] = alert_hammer+alert_high
	return df['alert']

def custom_trend(open,high,low,close):
	#(high_time,last_high,low_time,last_low,int_time,color = <1:green|0:red>)
	ind_arr = open.index.array
	open = open.array
	high = high.array
	low = low.array
	close = close.array
	lines = []
	line = None
	last_high = 0.0
	last_low = 100 * high[0]
	cur_high = high[0]
	cur_low = low[0]
	dir_up = False
	high_time = ind_arr[0]
	low_time = ind_arr[0]
	def add_line(i):
		color = 0 if dir_up else 1
		l = (high_time, last_high, low_time, last_low, ind_arr[i], color)
		lines.append(l)
		return l
	def remove_line(line):
		if line in lines:
			lines.remove(line)
	for i in range(1,len(ind_arr)):
		if dir_up:
			if high[i] > cur_high and low[i] < cur_low:
				pass
			elif low[i] < cur_low:
				last_low = low[i]
				cur_low = low[i]
				cur_high = high[i]
				low_time = ind_arr[i]
				remove_line(line)
				line = add_line(i)
			elif (high[i] > cur_high):
				last_high = high[i]
				cur_high = high[i]
				cur_low = low[i]
				high_time = ind_arr[i]
				dir_up = False
				line = add_line(i)
		if not dir_up:
			if (high[i] > cur_high and low[i]  < cur_low):
				pass
			elif (high[i] > cur_high):
				last_high = high[i]
				cur_high = high[i]
				cur_low = low[i]
				high_time = ind_arr[i]
				remove_line(line)
				line = add_line(i)
				
			elif low[i] < cur_low:
				last_low = low[i]
				cur_high = high[i]
				cur_low = low[i]
				low_time = ind_arr[i]
				dir_up = True
				line = add_line(i)
	return lines
# %%			
def fractals(open,high,low,close,n=2):
	df = pd.DataFrame()
	df['open'] = open
	df['high'] = high
	df['low'] = low
	df['close'] = close
	
	df['upFractal'] = (((high.shift(n-2)  < high.shift(n)) & (high.shift(n-1)  < high.shift(n)) & (high.shift(n+1) < high.shift(n)) & (high.shift(n+2) < high.shift(n)))
		| ((high.shift(n-3)  < high.shift(n)) & (high.shift(n-2)  < high.shift(n)) & (high.shift(n-1) == high.shift(n)) & (high.shift(n+1) < high.shift(n)) & (high.shift(n+2) < high.shift(n)))
		| ((high.shift(n-4)  < high.shift(n)) & (high.shift(n-3)  < high.shift(n)) & (high.shift(n-2) == high.shift(n)) & (high.shift(n-1) <= high.shift(n)) & (high.shift(n+1) < high.shift(n)) & (high.shift(n+2) < high.shift(n)))
		| ((high.shift(n-5) < high.shift(n)) & (high.shift(n-4)  < high.shift(n)) & (high.shift(n-3) == high.shift(n)) & (high.shift(n-2) == high.shift(n)) & (high.shift(n-1) <= high.shift(n)) & (high.shift(n+1) < high.shift(n)) & (high.shift(n+2) < high.shift(n)))
		| ((high.shift(n-6) < high.shift(n)) & (high.shift(n-5) < high.shift(n)) & (high.shift(n-4) == high.shift(n)) & (high.shift(n-3) <= high.shift(n)) & (high.shift(n-2) == high.shift(n)) & (high.shift(n-1) <= high.shift(n)) & (high.shift(n+1) < high.shift(n)) & (high.shift(n+2) < high.shift(n))))

	df['dnFractal'] = (( (low.shift(n-2)  > low.shift(n)) & (low.shift(n-1)  > low.shift(n)) & (low.shift(n+1) > low.shift(n)) & (low.shift(n+2) > low.shift(n)))
		| ((low.shift(n-3)  > low.shift(n)) & (low.shift(n-2)  > low.shift(n)) & (low.shift(n-1) == low.shift(n)) & (low.shift(n+1) > low.shift(n)) & (low.shift(n+2) > low.shift(n)))
		| ((low.shift(n-4)  > low.shift(n)) & (low.shift(n-3)  > low.shift(n)) & (low.shift(n-2) == low.shift(n)) & (low.shift(n-1) >= low.shift(n)) & (low.shift(n+1) > low.shift(n)) & (low.shift(n+2) > low.shift(n)))
		| ((low.shift(n-5) > low.shift(n)) & (low.shift(n-4)  > low.shift(n)) & (low.shift(n-3) == low.shift(n)) & (low.shift(n-2) == low.shift(n)) & (low.shift(n-1) >= low.shift(n)) & (low.shift(n+1) > low.shift(n)) & (low.shift(n+2) > low.shift(n)))
		| ((low.shift(n-6) > low.shift(n)) & (low.shift(n-5) > low.shift(n)) & (low.shift(n-4) == low.shift(n)) & (low.shift(n-3) >= low.shift(n)) & (low.shift(n-2) == low.shift(n)) & (low.shift(n-1) >= low.shift(n)) & (low.shift(n+1) > low.shift(n)) & (low.shift(n+2) > low.shift(n))))
	df['upFractal'] = df['upFractal'].apply(lambda x: 100 if x else 0)
	df['dnFractal'] = df['dnFractal'].apply(lambda x: -100 if x else 0)
	result = df['upFractal'] + df['dnFractal']
	return result

if __name__ == "__main__":
	import os
	os.chdir('..')
	from algotrader.db.util import *
	v = get_ohlc("HDFCBANK",from_d=dt.now()-timedelta(days=20),to_d=dt.now(),interval=OHLCInterval.Minute_15)
	val = fractals(v.open,v.high,v.low,v.close)
	print(v)
	print(val)
	# for i in val:
	# 	print(i)


# %%
