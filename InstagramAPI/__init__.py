#!/usr/bin/env python
# -*- coding: utf-8 -*-

import hashlib
import hmac
import json
import logging
import sys
import urllib
import uuid

import requests

# The urllib library was split into other modules from Python 2 to Python 3
if sys.version_info.major == 3:
    import urllib.parse


class InstagramAPI(object):
    API_URL = 'https://i.instagram.com/api/v1/'
    DEVICE_SETTINTS = {
        'manufacturer': 'Xiaomi',
        'model': 'HM 1SW',
        'android_version': 18,
        'android_release': '4.3'
    }
    USER_AGENT = 'Instagram 10.26.0 Android ({android_version}/{android_release}; 320dpi; 720x1280; {manufacturer}; {model}; armani; qcom; en_US)'.format(
        **DEVICE_SETTINTS)
    IG_SIG_KEY = '4f8732eb9ba7d1c8e8897a75d6474d4eb3f5279137431b2aafb71fafe2abe178'
    SIG_KEY_VERSION = '4'

    # username            # Instagram username
    # password            # Instagram password
    # uuid                # UUID
    # device_id           # Device ID
    # username_id         # Username ID
    # token               # _csrftoken
    # isLoggedIn          # Session status

    def __init__(self, username, password):
        m = hashlib.md5()
        m.update(username.encode('utf-8') + password.encode('utf-8'))
        self.device_id = self.generate_device_id(m.hexdigest())
        self.set_user(username, password)
        self.isLoggedIn = False

    def set_user(self, username, password):
        self.username = username
        self.password = password
        self.uuid = self.generate_uuid(True)

    def login(self, force=False):
        if (not self.isLoggedIn or force):
            self.s = requests.Session()
            # if you need proxy make something like this:
            # self.s.proxies = {"https" : "http://proxyip:proxyport"}
            resp = self.send_request('si/fetch_headers/?challenge_type=signup&guid=' + self.generate_uuid(False),
                                     login=True)
            if resp.status_code == 200:

                data = {'phone_id': self.generate_uuid(True),
                        '_csrftoken': resp.cookies['csrftoken'],
                        'username': self.username,
                        'guid': self.uuid,
                        'device_id': self.device_id,
                        'password': self.password,
                        'login_attempt_count': '0'}

                login_resp = self.send_request('accounts/login/', self.generate_signature(json.dumps(data)), True)
                if login_resp:
                    self.isLoggedIn = True
                    self.username_id = login_resp.json()["logged_in_user"]["pk"]
                    self.rank_token = "%s_%s" % (self.username_id, self.uuid)
                    self.token = resp.cookies["csrftoken"]

                    self.sync_features()
                    logging.info("Login success!\n")
                    return True
            else:
                raise Exception("Could not login!")

    def sync_features(self):
        data = json.dumps({
            '_uuid': self.uuid,
            '_uid': self.username_id,
            'id': self.username_id,
            '_csrftoken': self.token
        })
        return self.send_request('qe/sync/', self.generate_signature(data))

    def logout(self):
        logout = self.send_request('accounts/logout/')

    def media_info(self, mediaId):
        data = json.dumps({
            '_uuid': self.uuid,
            '_uid': self.username_id,
            '_csrftoken': self.token,
            'media_id': mediaId
        })
        return self.send_request('media/' + str(mediaId) + '/info/', self.generate_signature(data))

    def comment(self, mediaId, commentText):
        data = json.dumps({
            '_uuid': self.uuid,
            '_uid': self.username_id,
            '_csrftoken': self.token,
            'comment_text': commentText
        })
        return self.send_request('media/' + str(mediaId) + '/comment/', self.generate_signature(data))

    def delete_comment(self, mediaId, commentId):
        data = json.dumps({
            '_uuid': self.uuid,
            '_uid': self.username_id,
            '_csrftoken': self.token
        })
        return self.send_request('media/' + str(mediaId) + '/comment/' + str(commentId) + '/delete/',
                                 self.generate_signature(data))

    def get_media_likers(self, mediaId):
        likers = self.send_request('media/' + str(mediaId) + '/likers/?')
        return likers

    def search_tags(self, query):
        query = self.send_request(
            'tags/search/?is_typeahead=true&q=' + str(query) + '&rank_token=' + str(self.rank_token))
        return query

    def get_hashtag_feed(self, hashtagString, maxid=''):
        return self.send_request('feed/tag/' + hashtagString + '/?max_id=' + str(
            maxid) + '&rank_token=' + self.rank_token + '&ranked_content=true&')

    def like(self, mediaId):
        data = json.dumps({
            '_uuid': self.uuid,
            '_uid': self.username_id,
            '_csrftoken': self.token,
            'media_id': mediaId
        })
        return self.send_request('media/' + str(mediaId) + '/like/', self.generate_signature(data))

    def unlike(self, mediaId):
        data = json.dumps({
            '_uuid': self.uuid,
            '_uid': self.username_id,
            '_csrftoken': self.token,
            'media_id': mediaId
        })
        return self.send_request('media/' + str(mediaId) + '/unlike/', self.generate_signature(data))

    def get_media_comments(self, mediaId, max_id=''):
        return self.send_request('media/' + str(mediaId) + '/comments/?max_id=' + max_id)

    def get_liked_media(self, maxid=''):
        return self.send_request('feed/liked/?max_id=' + str(maxid))

    def generate_signature(self, data, skip_quote=False):
        if not skip_quote:
            try:
                parsedData = urllib.parse.quote(data)
            except AttributeError:
                parsedData = urllib.quote(data)
        else:
            parsedData = data
        return 'ig_sig_key_version=' + self.SIG_KEY_VERSION + '&signed_body=' + hmac.new(
            self.IG_SIG_KEY.encode('utf-8'), data.encode('utf-8'), hashlib.sha256).hexdigest() + '.' + parsedData

    def generate_device_id(self, seed):
        volatile_seed = "12345"
        m = hashlib.md5()
        m.update(seed.encode('utf-8') + volatile_seed.encode('utf-8'))
        return 'android-' + m.hexdigest()[:16]

    def generate_uuid(self, type):
        # according to https://github.com/LevPasha/Instagram-API-python/pull/16/files#r77118894
        # uuid = '%04x%04x-%04x-%04x-%04x-%04x%04x%04x' % (random.randint(0, 0xffff),
        #    random.randint(0, 0xffff), random.randint(0, 0xffff),
        #    random.randint(0, 0x0fff) | 0x4000,
        #    random.randint(0, 0x3fff) | 0x8000,
        #    random.randint(0, 0xffff), random.randint(0, 0xffff),
        #    random.randint(0, 0xffff))
        generated_uuid = str(uuid.uuid4())
        if (type):
            return generated_uuid
        else:
            return generated_uuid.replace('-', '')

    def send_request(self, endpoint, post=None, login=False):
        if (not self.isLoggedIn and not login):
            raise Exception("Not logged in!\n")

        self.s.headers.update({'Connection': 'close',
                               'Accept': '*/*',
                               'Content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
                               'Cookie2': '$Version=1',
                               'Accept-Language': 'en-US',
                               'User-Agent': self.USER_AGENT})
        print(self.API_URL + endpoint)
        if (post != None):  # POST
            response = self.s.post(self.API_URL + endpoint, data=post)  # , verify=False
        else:  # GET
            response = self.s.get(self.API_URL + endpoint)  # , verify=False
        return response

    def is_user_commented(self, media_id):
        resp = self.get_media_comments(media_id)
        comments = resp.json()["comments"]
        return self.username in [comment["user"]["username"] for comment in comments]

    def get_total_liked_media(self, scan_rate=1):
        next_id = ''
        liked_items = []
        for x in range(0, scan_rate):
            resp = self.get_liked_media(next_id)
            try:
                next_id = resp["next_max_id"]
                for item in resp["items"]:
                    liked_items.append(item)
            except KeyError as e:
                break
        return liked_items

    @staticmethod
    def extract_media_ids_from_items(items):
        for item in items:
            yield item["pk"]

    @staticmethod
    def extract_media_codes_from_items(items):
        for item in items:
            yield item["code"]
