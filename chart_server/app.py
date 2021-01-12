# app.py
from flask import Flask, request, jsonify, render_template
import pytz
import pymongo
from bson.codec_options import CodecOptions
from chart_server.static.config import config as cfg
import logging

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







chart_server = Flask(__name__)

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
    minute_db = CLIENT['NSE_DB_MINUTE'].with_options(codec_options=CodecOptions(tz_aware=True, tzinfo=TIMEZONE),read_concern=pymongo.read_concern.ReadConcern('local'))
    data = list(minute_db.list_collection_names())
    # log.info(data)
    return jsonify(data)



# A welcome message to test our server
@chart_server.route('/')
def index():
    
    return render_template("index.html")

if __name__ == '__main__':
    # Threaded option to enable multiple instances for multiple user access support
    chart_server.run(threaded=True, port=5000)