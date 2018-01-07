from config import *
import boto3
from flask import Flask, jsonify, render_template
import re
import time
import os
import pandas as pd

# EB looks for an 'application' callable by default.
application = Flask(__name__)
S3 = boto3.resource('s3', region_name=AWS_REGION,
                     aws_access_key_id=AWS_ACCESS_KEY_ID,
                     aws_secret_access_key=AWS_SECRET_ACCESS_KEY)

def _download_market_data(market_data_pairs):
    start_time = time.time()
    print("Downloading data from S3 for {} pairs".format(len(market_data_pairs)))
    for market_data_pair in market_data_pairs:
        filepath = "/".join([BASE_DIR, market_data_pair])
        try:
            S3.meta.client.download_file(
                Bucket=S3_BUCKET,
                Key=market_data_pair,
                Filename=filepath) 
        except Exception as e:
            print("Something went wrong went fetching {} from S3, error was {}".format(market_data_pair, e))
    print("Done downloading market data in {} minutes".format((time.time() - start_time)/60))
    return

def _parse_objects(objects):
    parsed_objects = []
    if objects and "Contents" in objects and objects["Contents"]:
        parsed_objects = [object["Key"] for object in objects.get("Contents", []) if "Key" in object] 
    return parsed_objects

@application.route("/download")
@application.route("/download/<currency>")
def download_market_data(currency=None):
    try:
        all_market_data_pairs_raw = S3.meta.client.list_objects_v2(Bucket=S3_BUCKET)
    except Exception as e:
        print("Could not fetch data from S3, error was {}".format(e))
        return jsonify({"success": False})
    all_market_data_pairs = _parse_objects(all_market_data_pairs_raw)
    if currency:
        market_data_pairs = filter(lambda x: re.search(r'^\w+-{}$'.format(currency), x), all_market_data_pairs)
        if market_data_pairs:
            _download_market_data(list(market_data_pairs))
        else:
            print("No market data for {} in S3".format(currency))
    else:
        _download_market_data(all_market_data_pairs)
    return jsonify({"success": True})
 
def _parse_market(market):
    if not market:
        return {}
    base_currency, market_currency = market.split("-")
    if not base_currency or not market_currency:
        print("Malformed market {}".format(market))
        return {}
    return({"base_currency": base_currency, "market_currency": market_currency})

def _format_market_data(market_data, market, sparkline_length):
    parsed_market = _parse_market(market)
    if not parsed_market:
        return {}
    formatted_data = {"market": market}
    formatted_data["base_currency"] = parsed_market["base_currency"]
    formatted_data["market_currency"] = parsed_market["market_currency"]
    if market_data:
        formatted_data["last"] = "{0:.2f}".format(market_data[-1])
        if len(market_data) >= sparkline_length:
            formatted_data["sparkline"] = market_data[-sparkline_length:] 
        all_emas = _get_emas(market_data, 60*60/FREQ_MARKET_DATA_UPDATE)
        if all_emas:
            formatted_data["relative_to_1h_ema"] = "{0:.2f}".format(100*(market_data[-1]/all_emas[-1] -1))
    return formatted_data

def _get_emas(market_data, period):
    if not market_data:
        return []
    alpha = 2/(period+1)
    all_emas = [market_data[0]]
    for i in range(1, len(market_data)):
        all_emas.append(alpha*market_data[i] + (1-alpha)*all_emas[i-1])
    return all_emas
    
@application.route('/markets')
def market_overview():
    start_time = time.time()
    all_market_data = {}
    sparkline_length = int(90*60/float(FREQ_MARKET_DATA_UPDATE))
    for market in os.listdir(BASE_DIR):
        try:
            market_data = pd.read_csv("/".join([BASE_DIR, market]))
        except Exception as e:
            print("Could not read data for market {}".format(market_data_csv))
            continue
        bid_data = list(market_data.bid) 
        formatted_data = _format_market_data(bid_data, market, sparkline_length)
        if not formatted_data:
            continue
        if not formatted_data["base_currency"] in all_market_data:
            all_market_data[formatted_data["base_currency"]] = []
        all_market_data[formatted_data["base_currency"]].append(formatted_data)
        print("Finished processing {} market data".format(market))
    print("Finished processing all market data in {} seconds".format(time.time()-start_time))
    all_markets = sorted(all_market_data.keys())
    flattened_market_data = [{
        "base_currency": base_currency,
        "currencies": sorted(all_market_data[base_currency], key=lambda x: -float(x["relative_to_1h_ema"]))} \
            for base_currency in all_markets]
    return jsonify({"success": True, "markets": flattened_market_data})

@application.route('/')
def overview():
    return render_template("overview.html")

# run the app.
if __name__ == "__main__":
    application.debug = True # remove in prod
    application.run()
