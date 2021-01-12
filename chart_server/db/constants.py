class CustomEnum(set):
	def __getattr__(self, name):
		if name in self:
			return name
		raise AttributeError
	def __setattr__(self, name, value):
		raise RuntimeError("Cannot override values")
	def __delattr__(self, name):
		raise RuntimeError("Cannot delete values")

class OHLCInterval(CustomEnum):
	Tick = 'tick'
	Minute_1 = 'minute'
	Minute_2 = '2minute'
	Minute_3 = '3minute'
	Minute_4 = '4minute'
	Minute_5 = '5minute'
	Minute_10 = '10minute'
	Minute_15 = '15minute'
	Minute_30 = '30minute'
	Minute_60 = '60minute'
	Hour_2 = '120minute'
	Hour_3 = '180minute'
	Hour_4 = '240minute'
	Day_1 = 'day'
	Week_1 = '1week'
	Month_1 = '1month'

	interval_list = ['tick',
					'minute',
					'2minute',
					'3minute',
					'4minute',
					'5minute',
					'10minute',
					'15minute',
					'30minute',
					'60minute',
					'120minute',
					'180minute',
					'240minute',
					'day',
					'1week',
					'1month',
					]

	@staticmethod
	def parseNew(str):
		str = str.upper()
		if str == 'TICK':
			return 'tick'
		if str == 'MINUTE':
			return 'minute'
		if str == '2MINUTE':
			return '2minute'
		if str == '3MINUTE':
			return '3minute'
		if str == '4MINUTE':
			return '4minute'
		if str == '5MINUTE':
			return '5minute'
		if str == '10MINUTE':
			return '10minute'
		if str == '15MINUTE':
			return '15minute'
		if str == '30MINUTE':
			return '30minute'
		if str == '60MINUTE' or str == '1HOUR' or str == 'HOUR':
			return '60minute'
		if str == '120MINUTE' or str == '2HOUR':
			return '120minute'
		if str == '180MINUTE' or str == '3HOUR':
			return '180minute'
		if str == '240MINUTE' or str == '3HOUR':
			return '240minute'
		if str == 'DAY':
			return 'day'
		if str == '1WEEK':
			return "week"
		if str == '1MONTH':
			return "month"
		return None


DB_NAMES = {
	OHLCInterval.Day_1 : 'NSE_DB_DAY',
	OHLCInterval.Minute_60 : 'NSE_DB_HOUR',
	OHLCInterval.Minute_1 : 'NSE_DB_MINUTE',
	OHLCInterval.Tick : 'TICKS_DB',
	}

ResampleInterval = {
	OHLCInterval.Minute_1 : ('1Min',0),
	OHLCInterval.Minute_2 : ('2Min',1),
	OHLCInterval.Minute_3 : ('3Min', 0),
	OHLCInterval.Minute_4 : ('4Min', 3),
	OHLCInterval.Minute_5 : ('5Min', 0),
	OHLCInterval.Minute_10 : ('10Min', 5),
	OHLCInterval.Minute_15 : ('15Min', 0),
	OHLCInterval.Minute_30 : ('30Min', 15),
	OHLCInterval.Minute_60 : ('60Min', 15),
	OHLCInterval.Hour_2 : ('120Min', 15),
	OHLCInterval.Hour_3 : ('180Min', 15),
	OHLCInterval.Hour_4 : ('240Min', 15),
	OHLCInterval.Day_1 : ('D', 0),
	OHLCInterval.Week_1 : ('W-SUN',7),
	OHLCInterval.Month_1 : ('M',0),
}

IntervalMinutes = {
	OHLCInterval.Minute_1 : 1,
	OHLCInterval.Minute_2 : 2,
	OHLCInterval.Minute_3 : 3,
	OHLCInterval.Minute_4 : 4,
	OHLCInterval.Minute_5 : 5,
	OHLCInterval.Minute_10 : 10,
	OHLCInterval.Minute_15 : 15,
	OHLCInterval.Minute_30 : 30,
	OHLCInterval.Minute_60 : 60,
	OHLCInterval.Hour_2 : 120,
	OHLCInterval.Hour_3 : 180,
	OHLCInterval.Hour_4 : 240,
	OHLCInterval.Day_1 : 1440,
	OHLCInterval.Week_1 : 10080,
	OHLCInterval.Month_1 : 43200,
}