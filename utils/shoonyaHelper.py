from shared_libraries.api_helper import ShoonyaApiPy

import logging
import json
import yaml
import signal
import os, sys, time
import pyotp
from datetime import date, datetime, timedelta
import pandas as pd
import math
import math
from scipy.stats import norm

sys.path.append('/home/kushy/Syncthing/Projects/Shoonya/')
from shared_libraries.helper_scripts import consulHelper, misc
from shared_libraries.helper_scripts.mibianLib import mibian

apkversion = "1.0.0"


# # ret = api.login(userid=uid, password=pwd, twoFA=factor2, vendor_code=vc, api_secret=app_key, imei=imei)
# with open('cred.yml') as f:
#     cred = yaml.load(f, Loader=yaml.FullLoader)
#     print(cred)


# totp = pyotp.TOTP(cred['totp_key']).now()
# # print(f'totp is {totp}')
# ret = api.login(userid = cred['user'], password = cred['pwd'], twoFA=totp, vendor_code=cred['vc'], api_secret=cred['api_key'], imei=cred['imei'])
# # ret = api.logout()
# # ret = 'x'


def checkMaxLoss(pnl):
    print(f'checking max loss with pnl {pnl}')
    try:
        with open('/tmp/maxLoss') as f:
            maxLoss = float(f.readlines()[0].strip('\n'))
            print(f'maxloss is {maxLoss}')
        if pnl == 'NA' or pnl == -1:
            return
        elif pnl < -1 * maxLoss:
            print('max loss crossed')
            ret = api.logout()
            exit(0)
    except Exception as e:
        print(f'error is {e}')


def getTradeCount(api):
    ret = api.get_trade_book()

    if ret is None:
        return 0

    order_uid = []
    count = 0
    for order in ret:
        order_id = order.get('norenordno')
        if (order_id not in order_uid):
            order_uid.append(order_id)
            if order['trantype'] == "B":
                count = count + 1
    return count


def getOptionsBrokerage(buy_turnover, sell_turnover):
    turnover = buy_turnover + sell_turnover
    stt = round(0.000625 * sell_turnover, 0)
    transct_charges = round(.0005 * turnover, 2)
    sebi = round(.000001 * turnover, 2)
    gst = round(.18 * (transct_charges + sebi), 2)
    stamp_duty = round(.00003 * buy_turnover, 0)
    ipf = round(.000005 * turnover, 2)
    # print(f'stt {stt} trans {transct_charges} gst {gst} sebi {sebi} stamp {stamp_duty} ipf {ipf}')
    # print(f'turnover is {turnover}, sell turnover is {sell_turnover}')
    brokerage = stt + transct_charges + gst + sebi + stamp_duty + ipf
    return brokerage


def getFuturesBrokerage(turnover, sell_turnover):
    brokerage = turnover * 0.0000246 + .0001 * sell_turnover
    return brokerage


def getCurrentTradeBook(api):
    return api.get_trade_book()


def getBrokerage(api):
    ret = api.get_limits()
    brokerage = 0
    if 'brokerage' in ret:
        brokerage = ret['brokerage']
    return float(brokerage)


def getBrokerage_old(api):
    ret = api.get_trade_book()
    order_uid = []
    sell_turnover, buy_turnover, turnover = 0, 0, 0

    # if(ret[0]['trantype'] == 'B'):
    #     return -1

    if ret is None:
        return 0
    for order in ret:
        order_id = order.get('norenordno')
        if (order_id not in order_uid):
            order_uid.append(order_id)
            qty = int(order['qty'])
            premium_prc = float(order['avgprc'])
            turnover = turnover + premium_prc * qty
            if order['trantype'] == "S":
                sell_turnover += premium_prc * qty
            else:
                buy_turnover += premium_prc * qty
    return getOptionsBrokerage(buy_turnover, sell_turnover)


def getPnl(api):
    ret = api.get_positions()
    if ret == None:
        return 0
        # return 1000
    pnl, mtm = 0, 0
    for position in ret:
        pnl += float(position['rpnl'])
        mtm += float(position['urmtom'])

    return round(pnl + mtm - getBrokerage(api))


def getDailyInfo():
    pnl = getPnl()
    brokerage = getBrokerage()
    tradebook = getTradebook()
    return pnl, tradebook


# import random
def getEma(api, exchange, token, length):
    # get price info from day start till now
    dayStart = datetime.today().replace(hour=9, minute=15, second=0, microsecond=0)
    endTime = datetime.now()

    while True:
        try:
            ret = api.get_time_price_series(exchange=exchange, token=token, starttime=dayStart.timestamp(),
                                            endtime=endTime.timestamp(), interval=length)
            break
        except Exception:
            print('Error Fetching information to get ema')
            time.sleep(1)
            continue

    if ret == None:
        return
        # return random.randint(1,10)

    ret = api.get_time_price_series(exchange, token, starttime=dayStart.timestamp(), endtime=endTime.timestamp(),
                                    interval=length)
    df = pd.DataFrame(ret).iloc[::-1]
    df['ema'] = df['intc'].ewm(span=8, adjust=False).mean()
    ema = df['ema'][0]
    return ema


def getDelta(spot, strike):
    current_date = datetime.now().strftime('%d-%m-%y')
    expiry_date = misc.get_nse_weekly_expiry('NIFTY', 0)

    # expiry = datetime.strptime(expiry_date, '%d-%m-%y').replace(hour=15, minute=30, second=0, microsecond=0)
    expiry = expiry_date.replace(hour=15, minute=30, second=0, microsecond=0)
    now = datetime.strptime(current_date, '%d-%m-%y')

    seconds = math.floor((expiry - now).total_seconds())
    minutes = math.floor(seconds / 60)
    hours = math.floor(minutes / 60)
    days = seconds / 86400

    c = mibian.BS([spot, strike, 7, days], volatility=18)
    return c.callDelta


def latestCE():
    spot = consulHelper.getConsulVar('shoonya/nifty_ltp')
    strike = int(float(spot) / 50) * 50
    # print(spot,strike)

    delta = getDelta(spot, strike)
    while (delta > 0.5):
        strike += 50
        delta = getDelta(spot, strike)

    while (delta < 0.35):
        strike -= 50
        delta = getDelta(spot, strike)

    return str(strike) + 'CE', delta


def latestPE():
    spot = consulHelper.getConsulVar('shoonya/nifty_ltp')
    strike = int(float(spot) / 50) * 50
    delta = 1 - getDelta(spot, strike)
    while (delta > 0.5):
        strike -= 50
        delta = 1 - getDelta(spot, strike)

    while (delta < 0.35):
        strike += 50
        delta = 1 - getDelta(spot, strike)
    return str(strike) + 'PE', delta


# deal with orders and positions


MAX_TRIES = 5


# modifyOrder(api, logger, i,'SL-LMT', qty, new_sl , new_sl + 0.2 )
# shoonyaHelper.modifyOrder(api, logger, order(norenordno='23110100127730', exch='NFO', tsym='NIFTY02NOV23P19050', qty='300', rorgqty=nan, ordenttm='1698811778', trantype='S', prctyp='SL-LMT', ret='DAY', token='50083', mult='1', prcftr='1.000000', instname='OPTIDX', ordersource='API', dname='NIFTY 02NOV23 19050 PE ', pp='2', ls='50', ti='0.05', prc='48.70', rorgprc=nan, rprc='48.70', avgprc=nan, dscqty='0', s_prdt_ali='NRML', prd='M', status='TRIGGER_PENDING', st_intrn='TRIGGER_PENDING', fillshares=nan, norentm='09:39:38 01-11-2023', exch_tm='01-11-2023 09:39:38', exchordid='1100000021068531', rqty='300', trgprc='48.90', remarks='stop_loss_order', rejreason=nan, rtrgprc=nan, cancelqty=nan), 'SL_LMT', 400, 48.525, 48.725)
# def modifyOrder(api, logger, order, newprice_type, qty=None, newprice=None, newtrigger_price=None):
def modifyOrder(api, logger, exch, tsym, norenordno, qty, newprice_type, newprice=None, newtrigger_price=None):
    res = {'rejreason': True}
    CURRENT_TRIES = 0

    try:
        if newprice_type == 'MKT':
            while res == None or 'rejreason' in res:
                logger.debug(
                    f"running command api.modify_order(exchange={exch}, tradingsymbol={tsym}, orderno={norenordno},\
                    newquantity={qty}, newprice_type='MKT', newprice=0.00)")
                res = api.modify_order(exchange=exch, tradingsymbol=tsym, orderno=norenordno,
                                       newquantity=qty, newprice_type='MKT', newprice=0.00)
                logger.info(f"res is {res}")

                CURRENT_TRIES += 1
                time.sleep(0.5)
                if CURRENT_TRIES >= MAX_TRIES:
                    logger.error('Max attempt to modify order failed')
                    break

        elif newprice_type == 'SL-LMT':
            while res == None or 'rejreason' in res:
                logger.debug(
                    f"running command api.modify_order(exchange={exch}, tradingsymbol={tsym}, orderno={norenordno}, \
                    newquantity={qty}, newprice_type='SL-LMT', newprice={newprice}, newtrigger_price={newtrigger_price})")
                res = api.modify_order(exchange=exch, tradingsymbol=tsym, orderno=norenordno,
                                       newquantity=qty, newprice_type='SL-LMT', newprice=newprice,
                                       newtrigger_price=newtrigger_price)
                logger.info(f"res is {res}")

                CURRENT_TRIES += 1
                time.sleep(0.5)
                if CURRENT_TRIES >= MAX_TRIES:
                    logger.error('Max attempt to modify order failed')
                    break

        elif newprice_type == 'LMT':
            while res == None or 'rejreason' in res:
                logger.debug(
                    f"running command api.modify_order(exchange={exch}, tradingsymbol={tsym}, orderno={norenordno}, \
                    newquantity={qty}, newprice_type='LMT', newprice={newprice})")
                res = api.modify_order(exchange=exch, tradingsymbol=tsym, orderno=norenordno,
                                       newquantity=qty, newprice_type='LMT', newprice=newprice)
                logger.info(f"res is {res}")

                CURRENT_TRIES += 1
                time.sleep(0.5)
                if CURRENT_TRIES >= MAX_TRIES:
                    logger.error('Max attempt to modify order failed')
                    break


    except Exception as err:
        print(f'error in modifying order {err}')
        logger.error(f'error in modifying order {err}')
    return res


def placeOrder(api, logger, order_type, product_type, exchange, tradingsymbol, quantity, newprice_type, price,
               trigger_price=None):
    ''' TODO:
        - fix market and lmt orders

    '''
    res = {'rejreason': True}
    CURRENT_TRIES = 0

    try:
        if newprice_type == 'MKT':
            while res == None or 'rejreason' in res:
                logger.debug(
                    f"running command api.place_order(buy_or_sell={order_type}, product_type={product_type}, exchange={exchange}, \
                     tradingsymbol={tradingsymbol}, quantity={quantity} , discloseqty=0 ,price_type='LMT', price=0.0, retention='DAY', remarks='market_order') ")

                res = api.place_order(buy_or_sell=order_type, product_type=product_type, exchange=exchange,
                                      tradingsymbol=tradingsymbol,
                                      quantity=quantity, discloseqty=0, price_type='MKT', price=0, trigger_price=None,
                                      retention='DAY', remarks='market_order')
                logger.info(f"res is {res}")

                CURRENT_TRIES += 1
                time.sleep(0.5)
                if CURRENT_TRIES >= MAX_TRIES:
                    logger.error('Max attempt to place order failed')
                    break

        elif newprice_type == 'SL-LMT':
            while res == None or 'rejreason' in res:
                logger.debug(
                    f"running command api.place_order(buy_or_sell={order_type}, product_type={product_type}, exchange={exchange},\
                     tradingsymbol={tradingsymbol}, quantity={quantity} , discloseqty=0 ,price_type='SL-LMT', price={price}, trigger_price={trigger_price}, retention='DAY', remarks='stop_loss_order')")
                res = api.place_order(buy_or_sell=order_type, product_type=product_type, exchange=exchange,
                                      tradingsymbol=tradingsymbol,
                                      quantity=quantity, discloseqty=0, price_type='SL-LMT', price=price,
                                      trigger_price=trigger_price,
                                      retention='DAY', remarks='stop_loss_order')
                logger.info(f"res is {res}")

                CURRENT_TRIES += 1
                time.sleep(0.5)
                if CURRENT_TRIES >= MAX_TRIES:
                    logger.error('Max attempt to place order failed')
                    break

        elif newprice_type == 'LMT':
            while res == None or 'rejreason' in res:
                logger.debug(
                    f"running command api.place_order(buy_or_sell={order_type}, product_type={product_type}, exchange={exchange},\
                     tradingsymbol={tradingsymbol},quantity={quantity} , discloseqty=0 ,price_type='LMT', price={price}, retention='DAY', remarks='limit_order')")
                res = api.place_order(buy_or_sell=order_type, product_type=product_type, exchange=exchange,
                                      tradingsymbol=tradingsymbol,
                                      quantity=quantity, discloseqty=0, price_type='LMT', price=price, retention='DAY',
                                      remarks='limit_order')
                logger.info(f"res is {res}")

                CURRENT_TRIES += 1
                time.sleep(0.5)
                if CURRENT_TRIES >= MAX_TRIES:
                    logger.error('Max attempt to place order failed')
                    break
    except Exception as err:
        print(f'error in placing order {err}')
        logger.error(f'error in placing order {err}')
    return res


def cancelOrder(api, logger, order):
    res = {'rejreason': True}
    CURRENT_TRIES = 0

    try:
        while ('rejreason' in res):
            orderno = order.norenordno  # from placeorder return value
            logger.debug(f"cancelling order {order}")
            res = api.cancel_order(orderno)
            logger.info(f"res is {res}")

            CURRENT_TRIES += 1
            time.sleep(0.5)
            if CURRENT_TRIES >= MAX_TRIES:
                logger.info('Max attempt to cancel order failed')
                break
    except Exception as err:
        print(f'error in cancelling order {err}')
        logger.error(f'error in cancelling order {err}')
    return res


def getOrderBook(api, logger):
    CURRENT_TRIES = 0

    try:
        ob = None
        while ob is None:
            ob = api.get_order_book()
            CURRENT_TRIES += 1
            time.sleep(0.1)
            if CURRENT_TRIES >= MAX_TRIES:
                logger.info('Max attempts to call orderbook api failed')
                break
    except Exception as err:
        print(f'error in getting orderbook {err}')
        logger.error(f'error in getting orderbook {err}')

    ob = pd.DataFrame(ob)
    return ob


def getOrder(api, orderno, logger):
    ob = getOrderBook(api, logger)
    for i in ob.itertuples():
        if i.norenordno == orderno:
            return i
    return


def getPositions(api, logger):
    CURRENT_TRIES = 0
    try:
        op = None
        while op is None:
            op = api.get_positions()
            CURRENT_TRIES += 1
            time.sleep(0.5)
            if CURRENT_TRIES >= MAX_TRIES:
                logger.info('Max attempts to call get_position api failed')
                break
    except Exception as err:
        # print(f'error in getting positions {err}')
        logger.error(f'error in getting positions {err}')

    op = pd.DataFrame(op)
    return op


def updateEma(api, token, hour, minute):
    exchange = 'NFO'
    multiplier = 0.092
    ema = 0
    # dayStart = datetime.today().replace(hour=9, minute=15, second=0, microsecond=0)
    # endTime = datetime.now()
    dayStart = (datetime.today() - timedelta(days=7)).replace(hour=9, minute=15, second=0, microsecond=0)
    # ret = api.get_time_price_series(exchange=exchange, token=token, starttime=dayStart.timestamp(), interval=1)

    endTime = datetime.today().replace(hour=hour, minute=minute, second=0, microsecond=0)
    # print(endTime)
    ret = api.get_time_price_series(exchange=exchange, token=token, starttime=dayStart.timestamp(),
                                    endtime=endTime.timestamp(), interval=1)

    df = pd.DataFrame(ret)
    df['intc'] = df['intc'].astype(float)

    for val in df['intc'][::-1]:
        ema = val * multiplier + ema * (1 - multiplier)
    # print(ema)
    return ema


def withdraw(api, logger, maxpay):
    CURRENT_TRIES = 0
    try:
        funds_payout = api.funds_payout(maxpay, str(maxpay * -100))
        logger.info(f"funds withdrawn")
    except Exception as err:
        # print(f'error in getting positions {err}')
        logger.error(f'error in withadrawing positions {err}')
