from datetime import datetime, timedelta
import os, sys, subprocess
import yaml
import math
import pandas as pd

import argparse
import docker
import requests
import nsepythonserver as nsp
import time
sys.path.append("/home/kushy/Syncthing/Projects/Shoonya/tradeParser/")
import mibian
import zipfile, requests, io
# from conf.config import logger
pd.set_option('mode.chained_assignment', None)

current_date = time.strftime("%Y-%m-%d")

class Misc:
    def __init__(self):
        self.nfo_file =  'Dependencies/' + 'NFO_' + str(current_date) + '.csv'
        self.bfo_file =  'Dependencies/' + 'BFO_' + str(current_date) + '.csv'
        self.nse_file =  'Dependencies/' + 'NSE_' + str(current_date) + '.csv'
        self.bse_file =  'Dependencies/' +'BSE_' + str(current_date) + '.csv'

        self.fileList  = [{"link":"https://api.shoonya.com/NFO_symbols.txt.zip", "name": "NFO_symbols.txt", "newName":self.nfo_file},
                          {"link":"https://api.shoonya.com/BFO_symbols.txt.zip", "name": "BFO_symbols.txt", "newName": self.bfo_file},
                          {"link":"https://api.shoonya.com/NSE_symbols.txt.zip", "name": "NSE_symbols.txt", "newName":self.nse_file},
                          {"link":"https://api.shoonya.com/BSE_symbols.txt.zip", "name": "BSE_symbols.txt", "newName":self.bse_file}]
        self.get_instrument_files()


    def get_instrument_files(self):
        global instrument_df
        current_date = time.strftime("%Y-%m-%d")
        expected_file = 'NFO_ ' + str(current_date) + '.csv'
        for item in os.listdir("Dependencies"):
            path = os.path.join(item)

            if item.endswith(".txt"):
                os.remove("Dependencies/" + path)

            elif (item.startswith('NFO_') or item.startswith('BFO_') or item.startswith('BSE_') or item.startswith('NSE_')) and (current_date not in item):
                if os.path.isfile("Dependencies/" + path):
                    os.remove("Dependencies/" + path)

        for expected_file in self.fileList:
            link, name, newName = expected_file['link'], expected_file['name'], expected_file['newName']
            # this will fetch instrument_df file from Dhan
            if not os.path.isfile(newName ):

                print("This BOT Is Picking New File From Shoonya")
                self.get_symbols_file(link, name,newName)

            # self.get_symbols_file("https://api.shoonya.com/NFO_symbols.txt.zip", "NFO_symbols.txt","NFO_"+ str(current_date) + '.csv')
            # self.get_symbols_file("https://api.shoonya.com/NSE_symbols.txt.zip", "NSE_symbols.txt","NSE_"+ str(current_date) + '.csv')
            # self.get_symbols_file("https://api.shoonya.com/BFO_symbols.txt.zip", "BFO_symbols.txt","BFO_"+ str(current_date) + '.csv')
            # self.get_symbols_file("https://api.shoonya.com/BSE_symbols.txt.zip", "BSE_symbols.txt","BSE_"+ str(current_date) + '.csv')

        # return instrument_df

    def get_symbols_file(self, url, filename, newname):
        response = requests.get(url)
        # Check if the request was successful
        if response.status_code == 200:
            # Extract the zip file contents
            with zipfile.ZipFile(io.BytesIO(response.content)) as z:
                z.extractall('Dependencies/')
            print("Zip file extracted successfully.")
            os.rename('Dependencies/' + filename,  newname)
        else:
            print("Failed to download the zip file.")

    def restart_container( self, config):
        bashCommandName = 'cat /tmp/container'
        container_id = subprocess.check_output(['bash', '-c', bashCommandName])
        print('restarting container with id ', container_id.decode("utf-8"))
        self.sendNotif(config, "encountered error", f"restarting container {container_id}")
        container_id = container_id.decode("utf-8")
        client = docker.from_env()
        container = client.containers.get(container_id)
        container.restart()


    def stop_container(self):
        bashCommandName = 'cat /tmp/container'
        container_id = subprocess.check_output(['bash', '-c', bashCommandName])
        print('stopping container with id ', container_id.decode("utf-8"))
        container_id = container_id.decode("utf-8")
        client = docker.from_env()
        container = client.containers.get(container_id)
        container.stop()


    def getHolidays(self):
        holiday_list = list()
        holidays = nsp.nse_holidays()['FO']
        df = pd.DataFrame(holidays)
        for date in df.tradingDate:
            date = datetime.strptime(date, '%d-%b-%Y').strftime('%d-%m-%y')
            holiday_list.append(date)
        return holiday_list


    # def getWorkingDates():
    #     working_days = list()
    #
    #     # holidays = config['holidays']
    #     holidays = consulHelper.getConsulVar('shoonya/const/holidays').replace('\'', '').split(',')
    #     # print(holidays)
    #     date = datetime.today()
    #     year = date.strftime('%y')
    #     week = date.isocalendar().week
    #
    #     while int(year) < 25:
    #         weekday = date.weekday()
    #         if weekday < 5 and date.strftime('%d-%m-%y') not in holidays:
    #             working_days.append(date.strftime('%d-%m-%y'))
    #         date = date + timedelta(days=1)
    #         year = date.strftime('%y')
    #         new_week = date.isocalendar().week
    #         if new_week != week:
    #             week = new_week
    #             working_days.append("")
    #         # print(date.strftime('%d-%m-%y'))
    #     return working_days


    def isValidDay(self, date):
        # holidays = consulHelper.getConsulVar('shoonya/const/holidays').replace('\'','').split(',')
        holidays = self.getHolidays()
        date_dt = datetime.strptime(date, '%d-%m-%y')
        if date in holidays:
            return False
        # if date_dt.weekday() > 4 and date not in weekend_but_active_days:
        if date_dt.weekday() > 4:
            return False

        return True


    def get_nse_weekly_expiry(self, symbol, week):
        df = pd.read_csv(self.nfo_file)

        df_index = df[df.Symbol == symbol]
        df_index['Expiry'] = df_index['Expiry'].apply(lambda x: datetime.strptime(x.title(), '%d-%b-%Y'))
        df_index = df_index.sort_values(by='Expiry')
        expiry_dates = df_index['Expiry'].unique()
        expiry_date = expiry_dates[week]
        current_date = datetime.today().date()
        if expiry_date.date() <= current_date  :
            # logger.info("today is expiry, shifting to next week")
            expiry_date = expiry_dates[week+1]
        return expiry_date


    def get_nse_monthly_expiry(self, symbol, month=0):
        df = pd.read_csv(self.nfo_file)

        df_index = df[df.Symbol == symbol]
        df_index['Expiry'] = df_index['Expiry'].apply(lambda x: datetime.strptime(x.title(), '%d-%b-%Y'))
        df_index = df_index.sort_values(by='Expiry')
        expiry_dates = df_index['Expiry'].unique()
        expiry_dates_fut = df_index[df_index['Instrument'] == 'FUTIDX']['Expiry'].unique()
        expiry_date = expiry_dates_fut[month]
        return expiry_date


    def get_bse_weekly_expiry(self, symbol, week):
        df = pd.read_csv(self.bfo_file)

        if symbol == 'SENSEX':
            symbol = 'BSXOPT'
        if symbol == 'BANKEX':
            symbol = 'BKXOPT'

        df_index = df[df.Symbol == symbol]
        df_index['Expiry'] = df_index['Expiry'].apply(lambda x: datetime.strptime(x.title(), '%d-%b-%Y'))
        df_index = df_index.sort_values(by='Expiry')
        expiry_dates = df_index['Expiry'].unique()
        expiry_date = expiry_dates[week]
        return expiry_date


    def get_bse_monthly_expiry(self, symbol, month=0):
        df = pd.read_csv(self.bfo_file)

        if symbol == 'SENSEX':
            symbol = 'BSXFUT'
        if symbol == 'BANKEX':
            symbol = 'BKXFUT'

        df_index = df[df.Symbol == symbol]
        df_index['Expiry'] = df_index['Expiry'].apply(lambda x: datetime.strptime(x.title(), '%d-%b-%Y'))
        df_index = df_index.sort_values(by='Expiry')
        expiry_dates = df_index['Expiry'].unique()
        expiry_dates_fut = df_index[df_index['Instrument'] == 'FUTIDX']['Expiry'].unique()
        expiry_date = expiry_dates_fut[month]
        return expiry_date


    def get_weekly_expiry(self, symbol, exchange, week=0):
        if exchange == 'NSE' or exchange == 'NFO':
            return self.get_nse_weekly_expiry(symbol, week)
        else:
            return self.get_bse_weekly_expiry(symbol, week)


    def get_monthly_expiry(self, symbol, exchange, month=0):
        if exchange == 'NSE' or exchange == 'NFO':
            return self.get_nse_monthly_expiry(symbol, month)
        else:
            return self.get_bse_monthly_expiry(symbol, month)


    def get_previous_expiry(self, symbol, current_expiry):
        expiries = self.gspreadHelper.get_expiry_list(symbol)
        expiries.reverse()

        for expiry in expiries:
            expiry_dt = datetime.strptime(expiry, '%d-%m-%y')
            if expiry_dt < current_expiry:
                return expiry_dt
        return


    # def getLatestMonthlyExpiry(date):
    #     expiries = consulHelper.getConsulVar('shoonya/const/monthly_expiries').replace('\'','')
    #     expiries = expiries.split(',')
    #     for expiry in expiries:
    #         # print(expiry)
    #         if datetime.strptime(expiry, '%d-%m-%y') >= datetime.strptime(date, '%d-%m-%y'):
    #             return expiry
    #     return


    def getLastMonthlyExpiry(self, date):
        expiries = self.consulHelper.getConsulVar('shoonya/const/monthly_expiries').replace('\'', '')
        expiries = expiries.split(',')
        prev_expiry = None
        for expiry in expiries:
            if datetime.strptime(expiry, '%d-%m-%y') >= datetime.strptime(date, '%d-%m-%y'):
                return prev_expiry
            prev_expiry = expiry
        return


    def getToken(self, tsym):
        df = pd.read_csv(self.nfo_file)
        df = df[df.TradingSymbol == tsym]
        if not df.empty:
            return str(df.iloc[0]['Token'])
        return


    def getFnoSymbol(df, token):
        df = df[df.Token == int(token)]
        if not df.empty:
            return df.iloc[0]['TradingSymbol']
        return


    def getSymbol(self, df, token):
        token = int(token)
        df = df[df.Token == int(token)]
        if not df.empty:
            return df.iloc[0]['TradingSymbol']
        return


    def getSpotSymbol(self, df, token):
        token = int(token)
        df = df[df.Token == int(token)]
        spot_symbol = ''
        if not df.empty:
            spot_symbol = df.iloc[0]['Symbol']

        if spot_symbol == 'BSXOPT':
            spot_symbol = 'SENSEX'
        if spot_symbol == 'BKXOPT':
            spot_symbol = 'BANKEX'
        return spot_symbol


    def getExchange(self, df, token):
        token = int(token)
        df = df[df.Token == int(token)]
        if not df.empty:
            return df.iloc[0]['Exchange']
        return


    def getOptionDelta(self, df, ltps, indexDict, token):
        token = int(token)
        tsym = self.getSymbol(df, token)
        option_type = tsym[-6]
        strike = int(tsym[-5:])

        spot_symbol = self.getSpotSymbol(df, token)
        exchange = self.getExchange(df, token)
        spot_token = str(indexDict[spot_symbol].spot_token)
        ltp = ltps[spot_token]

        delta = self.getDelta(ltp, strike, spot_symbol, exchange)
        if option_type == 'C':
            return delta
        return 1 - delta


    def get_future_ltp(self, df, ltps, indexDict, token):
        token = int(token)
        spot_symbol = df[df.Token == token].iloc[0]['Symbol']
        fut_token = indexDict[spot_symbol].fut_token
        return ltps[str(fut_token)]


    def getFutSl(self, df, indexDict, token):
        token = int(token)
        symbol = df[df.Token == token].iloc[0]['Symbol']

        if symbol == 'BSXOPT':
            symbol = 'SENSEX'

        fut_sl = indexDict[symbol].fut_sl
        return fut_sl


    def getTargets(self, df, indexDict, token):
        token = int(token)
        symbol = df[df.Token == token].iloc[0]['Symbol']

        if symbol == 'BSXOPT':
            symbol = 'SENSEX'

        targets = indexDict[symbol].targets
        return targets[0], targets[1], targets[2]


    def getMaxSl(self, df, indexDict, token):
        token = int(token)
        spot_symbol = self.getSpotSymbol(df, token)
        return indexDict[spot_symbol].max_sl


    def getDelta(self,spot, strike, spot_symbol, exchange):
        # current_date = (datetime.now().replace(hour=h, minute=m)).strftime('%d-%m-%y')
        now = datetime.now()
        expiry_date = self.get_weekly_expiry(spot_symbol, exchange)

        # expiry = datetime.strptime(expiry_date, '%d-%m-%y').replace(hour=15, minute=30, second=0, microsecond=0)
        expiry = expiry_date.replace(hour=15, minute=30, second=0, microsecond=0)

        # now = datetime.strptime(current_date, '%d-%m-%y')

        seconds = math.floor((expiry - now).total_seconds())
        minutes = math.floor(seconds / 60)
        hours = math.floor(minutes / 60)
        days = seconds / 86400

        c = mibian.BS([spot, strike, 7, days], volatility=18)
        return c.callDelta


    def sendNotif(self, config, title, body=None):
        if body is None:
            body = ''
        webhook_url = config['discord']['webhook_url']
        headers = {'content-type': 'application/json'}
        data = {"content": title + '\n' + body}
        r = requests.post(webhook_url, json=data, headers=headers)

misc = Misc()

# if __name__ == "__main__":
#     parser = argparse.ArgumentParser()
#     parser.add_argument('--sendNotif', action='store_true', default=None)
#     args = parser.parse_args()
#     if args.sendNotif is not None:
#         sendNotif('sample', 'notification')
