import time, yaml
from datetime import datetime
# from Dhan_Tradehull import Tradehull
from Dependencies.Dhan_Tradehull.Dhan_Tradehull import Tradehull
from utils.shoonyaApiHelper import ShoonyaApiPy
import pyotp
import logging

from utils.loggerHelper import setup_logger

with open('conf/config.yaml', 'r') as file:
    config = yaml.safe_load(file)

client_id = config['dhan']['client_id']
access_token = config['dhan']['access_token']


# Get logging level from conf
log_level_str = config.get('logging', {}).get('level', 'INFO')
log_level = getattr(logging, log_level_str.upper(), logging.INFO)

try:
    # dhan = dhanhq(client_id, acces_token)
    dhan_api = Tradehull(client_id, access_token, log_level)
    logger = dhan_api.logger
    shoonya_api = ShoonyaApiPy()
    # api.logout()
    cred = config['shoonya']
    totp = pyotp.TOTP(cred['totp_key']).now()
    ret = shoonya_api.login(userid = cred['user'], password = cred['pwd'], twoFA=totp,
                    vendor_code=cred['vc'], api_secret=cred['api_key'], imei=cred['imei'])
except Exception as err :
    print(f"encountered error on logging in {err}")
    exit(1)

ltps = dict()