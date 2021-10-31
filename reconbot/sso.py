import requests
import base64
import time
import yaml
import glob

class SSO:

    def __init__(self, client_id, secret_key, refresh_token, character_id):
        self.client_id = client_id
        self.secret_key = secret_key
        self.refresh_token = refresh_token
        self.login_server = 'https://login.eveonline.com'
        self.access_token = None
        self.access_token_expiry = None
        self.character_id = character_id

    def get_access_token(self):
        if self.token_expired():
            return self.fetch_access_token()

        return self.access_token

    def fetch_access_token(self):
        payload = {
            'grant_type': 'refresh_token',
            'refresh_token': self.refresh_token
        }
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'authorization': 'Basic %s' % base64.b64encode(str.encode('%s:%s' % (self.client_id, self.secret_key))).decode('utf-8')
        }

        r = requests.post('%s/v2/oauth/token' % self.login_server, data=payload, headers=headers)
        if r.status_code == 200:
            response = r.json()            
            self.access_token = response['access_token']
            self.access_token_expiry = self.set_token_expiry(response['expires_in'])
            if response['refresh_token'] != self.refresh_token:
                old_refresh = self.refresh_token
                self.refresh_token = response['refresh_token']
                self.update_refresh_token_in_yaml(old_refresh, self.refresh_token)

            return self.access_token
        else:
            r.raise_for_status()

    def set_token_expiry(self, seconds):
        self.access_token_expiry = time.time() + seconds
        return self.access_token_expiry

    def token_expired(self):
        return self.access_token_expiry == None or self.access_token_expiry <= time.time()

    def update_refresh_token_in_yaml(self, old_refresh, new_refresh):
        all_yamls = glob.glob('./*.yaml')
        for yamlpath in all_yamls:
            with open(yamlpath, 'r+') as file:
                toons = yaml.load(file)
                changed_token = False
                for toon in toons.values():
                    if toon['refresh_token'] == old_refresh:
                        toon['refresh_token'] = new_refresh
                        changed_token = True
                        break
                if changed_token:
                    yaml.dump(toons, file, default_flow_style=False)