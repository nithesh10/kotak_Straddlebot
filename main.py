from numpy import double
import creds
import requests
import pandas as pd
import ks_api_client
from ks_api_client import ks_api
from datetime import date
from datetime import datetime
from nsepython import *
import sys
import nse_fno_expiry_calculator as nf
#sys.setrecursionlimit(-1)


today = date.today()
d1 = today.strftime("%d%b%y")
d1=d1.upper()
print("Today's date:", d1.upper())


class recursion_depth:
    def __init__(self, limit):
        self.limit = limit
        self.default_limit = sys.getrecursionlimit()
    def __enter__(self):
        sys.setrecursionlimit(self.limit)
    def __exit__(self, type, value, traceback):
        sys.setrecursionlimit(self.default_limit)
#sys.stdout = open('logfile', 'w')
class Tee(object):
    def __init__(self, *files):
        self.files = files
    def write(self, obj):
        for f in self.files:
            f.write(obj)
f = open(f"temp/{datetime.datetime.now().strftime('mylogfile_%H_%M_%d_%m_%Y.txt')}", 'w')
backup = sys.stdout
sys.stdout = Tee(sys.stdout, f)


def get_atm_strike(symbol):
    symbol = symbol.upper()
    option_chain_json = nse_optionchain_scrapper(symbol)
    data = option_chain_json['filtered']['data']
    ltp = data[0]['PE']['underlyingValue']
    strike_price_list = [x['strikePrice'] for x in data]
    atm_strike = sorted([[round(abs(ltp-i),2),i] for i in strike_price_list])[0][1]
    return atm_strike

def get_pe_ce_price(symbol,atm_strike):
    symbol = symbol.upper()
    option_chain = nse_optionchain_scrapper(symbol)
    for dictt in option_chain['filtered']['data']:
        if dictt['strikePrice'] ==atm_strike:
            pe_price = dictt['PE']['askPrice']
            ce_price = dictt['CE']['askPrice']
    return pe_price,ce_price


kotak_ip = '127.0.0.1'
kotak_appId = 'DefaultApplication'
user_id = creds.USER_NAME
user_pwd = creds.PASSWORD
consumer_key = creds.CONSUMER_KEY
consumer_secret = creds.SECRET_KEY
access_token = creds.ACCESS_TOKEN
host = "https://tradeapi.kotaksecurities.com/apim"
try:
    client = ks_api.KSTradeApi(access_token = access_token, userid = user_id, \
                            consumer_key = consumer_key, ip = kotak_ip, app_id = kotak_appId, \
                            host = host, consumer_secret = consumer_secret)
except Exception as e:
    print("Exception when calling SessionApi->KSTradeApi: %s\n" % e)

try:
    # Login using password
    client.login(password = user_pwd)
except Exception as e:
    print("Exception when calling SessionApi->login: %s\n" % e)

try:
    # Generate final Session Token
    client.session_2fa()
except Exception as e:
    print("Exception when calling SessionApi->session_2fa: %s\n" % e)
"""
client = ks_api.KSTradeApi(access_token = creds.ACCESS_TOKEN, userid = creds.USER_NAME, consumer_key = creds.CONSUMER_KEY,ip = "127.0.0.1", app_id = creds.APP_ID, \
                            host = "https://tradeapi.kotaksecurities.com/apim", consumer_secret = creds.CONSUMER_KEY)
    # Initiate login and generate OTT
client.login(password = creds.PASSWORD)

    #Complete login and generate session token
client.session_2fa()
"""
print("bot logged in",client)
#generate_Session()




def token_info():
    today=nf.getNearestWeeklyExpiryDate()
    d1 = today.strftime("%d%b%y")
    d1=d1.upper()
    url =  'https://tradeapi.kotaksecurities.com/apim/scripmaster/1.1/filename'
    headers = {'accept' : 'application/json', 'consumerKey' : creds.CONSUMER_KEY, 'Authorization':f'Bearer {creds.ACCESS_TOKEN}'}
    res = requests.get(url,headers=headers).json()
    cashurl = res['Success']['cash']
    fnourl = res['Success']['fno']
    cashdf = pd.read_csv(cashurl,sep='|')
    fnodf = pd.read_csv(fnourl,sep='|')
    df=fnodf
    dff=pd.DataFrame()
    creds.token_info= df[((df["instrumentName"]==("BANKNIFTY")) | (df["instrumentName"]==("NIFTY")))]
    #creds.token_info.to_excel("tokens.xlsx")
    dff=creds.token_info[creds.token_info["instrumentName"]=="NIFTY"]
    creds.expiry=str(d1)
    print("nearest expiry",creds.expiry)
    dfz=cashdf
    creds.index_info= dfz[((dfz["instrumentName"]==("NIFTY 50")) | (dfz["instrumentName"]==("NIFTY BANK")))]
    dff=creds.index_info
    creds.nifty_token_instrument=dff['instrumentToken'].iat[0]
    creds.bank_nifty_token_instrument=dff['instrumentToken'].iat[1]

    print(creds.nifty_token_instrument)
    #print('today is '+str(datetime.datetime.now().date()))
    #print('nearest weekly exp is '+str(d1))

token_info()





def place_kotak_orders():

    print("placing order")
    creds.at_the_money_nifty=get_atm_strike("NIFTY")
    print("at the money",creds.at_the_money_nifty)
    dff=creds.token_info
    nifty_ce_token_instrument= dff[(dff["strike"]==(int(creds.at_the_money_nifty))) & (dff["expiry"]==((creds.expiry)))]
    creds.nifty_ce_token_instrument=nifty_ce_token_instrument["instrumentToken"].iat[0]
    creds.nifty_pe_token_instrument=nifty_ce_token_instrument["instrumentToken"].iat[1]
    print('at the money token instrument ce',creds.nifty_ce_token_instrument,"pe",creds.nifty_pe_token_instrument)
    quote=client.quote(instrument_token = int(creds.nifty_ce_token_instrument))
    creds.avg_price_nifty_ce=quote["success"][0]["ltp"]
    quote=client.quote(instrument_token = int(creds.nifty_pe_token_instrument))
    creds.avg_price_nifty_pe=quote["success"][0]["ltp"]
    print(creds.avg_price_nifty_ce)
    print(creds.avg_price_nifty_pe)
    try:
        ord_id=client.place_order(order_type = creds.order_type, instrument_token = int(creds.nifty_ce_token_instrument), transaction_type = "SELL",\
                   quantity = creds.quantity, price = 0, disclosed_quantity = 0, trigger_price = 0,\
                   tag = "string", validity = "GFD", variety = "REGULAR")
        creds.call=1
        print(ord_id,"Success")
        print("ORDER_ID",ord_id["Success"]["NSE"]["orderId"])
    except Exception as e:
        print("Error",e)
        #pass
    try:
        client.place_order(order_type = creds.order_type, instrument_token = int(creds.nifty_pe_token_instrument), transaction_type = "SELL",\
                   quantity = creds.quantity, price = 0, disclosed_quantity = 0, trigger_price = 0,\
                   tag = "string", validity = "GFD", variety = "REGULAR")
        creds.put=1
        print(ord_id,"Success")
        print("ORDER_ID",ord_id["Success"]["NSE"]["orderId"])

        check_stoploss()
    except Exception as e:
        #creds.call=1
        #creds.put=0
        print("Error",e)
        #pass
    check_stoploss()


    #creds.placed_orders.append(myorder["order_id"])
def check_stoploss():
         print("checking stoploss")
         from datetime import datetime
         import time
         while True:
            now= datetime.now()
            dt_string = now.strftime("%H:%M:%S")
            print(dt_string)
            end_time = creds.end_time
            if (datetime.now().hour * 60 + datetime.now().minute) >= end_time:
                print( "Trading day closed, time is above stop_time")
                if( creds.call==1):
                    try:
                        ord_id=client.place_order(order_type = creds.order_type, instrument_token = int(creds.nifty_ce_token_instrument), transaction_type = "BUY",\
                        quantity = creds.quantity, price = 0, disclosed_quantity = 0, trigger_price = 0,\
                        tag = "string", validity = "GFD", variety = "REGULAR")
                        print(ord_id)
                        creds.call=0

                    except Exception as e:
                        pass
                        print("Error",e)
                if(creds.put==1):
                    try:
                        ord_id=client.place_order(order_type = creds.order_type, instrument_token = int(creds.nifty_ce_token_instrument), transaction_type = "BUY",\
                        quantity = creds.quantity, price = 0, disclosed_quantity = 0, trigger_price = 0,\
                        tag = "string", validity = "GFD", variety = "REGULAR")
                        print(ord_id)
                        creds.put=0
                    except Exception as e:
                        pass
                        print("Error",e)
                exit()
            try:
                quote=client.quote(instrument_token = int(creds.nifty_ce_token_instrument))
                ltp=quote["success"][0]["ltp"]
            except:
                print("exception in fetching price details")
            if(creds.call==1):
                print("ltp",ltp,"avg_price",creds.avg_price_nifty_ce)
                print("% p/l",(double(creds.avg_price_nifty_ce)-double(ltp))*100/double(creds.avg_price_nifty_ce))
            if((double(creds.avg_price_nifty_ce)-double(ltp))*100/double(creds.avg_price_nifty_ce)<=creds.percent_sl) and creds.call==1:
                try:
                    ord_id=client.place_order(order_type = creds.order_type, instrument_token = int(creds.nifty_ce_token_instrument), transaction_type = "BUY",\
                    quantity = creds.quantity, price = 0, disclosed_quantity = 0, trigger_price = 0,\
                    tag = "string", validity = "GFD", variety = "REGULAR")
                    print(ord_id)
                    creds.call=0

                except Exception as e:
                    print("Error",e)
            try:
                bn_quote=client.quote(instrument_token = int(creds.nifty_pe_token_instrument))
                ltp=bn_quote["success"][0]["ltp"]
            except:
                print("exception in fetching price details")
            if(creds.put==1):
                print("ltp",ltp,"avg_price",creds.avg_price_nifty_pe)
                print("% p/l",(double(creds.avg_price_nifty_pe)-double(ltp))*100/double(creds.avg_price_nifty_pe))
            if((double(creds.avg_price_nifty_ce)-double(ltp))*100/double(creds.avg_price_nifty_ce)<=creds.percent_sl) and creds.put==1:
                try:
                    ord_id=client.place_order(order_type = creds.order_type, instrument_token = int(creds.nifty_ce_token_instrument), transaction_type = "BUY",\
                    quantity = creds.quantity, price = 0, disclosed_quantity = 0, trigger_price = 0,\
                    tag = "string", validity = "GFD", variety = "REGULAR")
                    print(ord_id)
                    creds.put=0
                except Exception as e:
                    print("Error",e)
            time.sleep(creds.sl_count)
def main():
    with recursion_depth(100000):
        print("main")
        def take_response():
            from datetime import datetime
            import time
            now= datetime.now().time()
            dt_string = now.strftime("%H:%M:%S")
            chktime = datetime.strptime(creds.check_time,'%H:%M:%S').time()
            remtime=(datetime.combine(date.today(), chktime) - datetime.combine(date.today(), now)).total_seconds()
            print("time to counter",datetime.combine(date.today(), chktime) - datetime.combine(date.today(), now))
            print("sleeping for",remtime)
            time.sleep(remtime)
            st=datetime.now()
            place_kotak_orders()
            #else:
            #    take_response()
        take_response()
main()