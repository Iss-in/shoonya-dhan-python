import requests
import time
from conf.config import config, logger
import urllib.parse
import json
# Configuration
PIHOLE_API_URL = "http://172.25.0.6/api"
PIHOLE_AUTH_URL = "http://172.25.0.6/api/auth"

API_TOKEN = "your-api-token"
REGEX_TO_BLOCK = "\\bexample\\.com\\b"  # Example regex to block

class Pihole:
    def __init__(self):
        self.password = config['pihole']['password']
        self.url = config['pihole']['url']
        self.sid = self.authenticate()
        self.headers = {
            "X-FTL-SID": self.sid
        }

    def authenticate(self):
        payload = {"password":self.password}
        response = requests.request("POST", PIHOLE_AUTH_URL, json=payload, verify=False)
        if "error" in response.json():
            logger.error("Pihole Authentication failed")
        else:
            sid =  response.json()["session"]["sid"]
            return sid
            return urllib.parse.quote(sid)

        return None

    def add_regex_to_blocklist(self, regex):
        payload = {
            "list": "regex_black",
            "add": regex,
            # "auth": API_TOKEN
        }
        response = requests.post(PIHOLE_API_URL,  headers=self.headers, data=payload, verify=False)
        if response.status_code == 200:
            print(f"Successfully added regex to blocklist: {regex}")
        else:
            print(f"Failed to add regex to blocklist: {regex}")
            print(response.text)

    def remove_regex_from_blocklist(self, regex):
        payload = {
            "list": "regex_black",
            "sub": regex,
            "auth": API_TOKEN
        }
        response = requests.post(PIHOLE_API_URL, data=payload, verify=False)
        if response.status_code == 200:
            print(f"Successfully removed regex from blocklist: {regex}")
        else:
            print(f"Failed to remove regex from blocklist: {regex}")
            print(response.text)

    def disablePihole(self):
        PIHOLE_API_URL = "http://172.25.0.6/api/dns/blocking"
        payload =  {
            "blocking":False,
            # "timer":25200
        }
        # payload = json.dumps(payload)
        response = requests.post(PIHOLE_API_URL, headers=self.headers, json=payload, verify=False)
        print(response.text)

    def enablePihole(self, seconds=25200):
        PIHOLE_API_URL = "http://172.25.0.6/api/dns/blocking"
        payload =  {
            "blocking":True,
            "timer":seconds
        }
        # payload = json.dumps(payload)
        response = requests.post(PIHOLE_API_URL, headers=self.headers, json=payload, verify=False)
        print(response.text)

    def blockForDuration(self, duration_minutes=15):
        '''
        enable blocking for dhan on a certain duration
        '''
        self.enablePihole(seconds = duration_minutes * 60)


pihole = Pihole()
pihole.disablePihole() # disable blocking on startup








