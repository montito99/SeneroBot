import unittest

import sys
from os.path import dirname

import yaml
sys.path.append(dirname(__file__))
from SeneroBot.senero_bot import SeneroBot


class TestBot(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with open("config.yaml") as conf_file:
            config = yaml.load(conf_file)

        cls.bot = SeneroBot(config["bot_creds"]["username"], config["bot_creds"]["password"], config["tags_to_search"])

    def test_comment(self):
        selected_post = self.bot.api.get_hashtag_feed("bitcoin").json()["items"][0]
        selected_post_id = selected_post["pk"]
        selected_post_code = selected_post["code"]
        test_string = "this is a test"
        self.bot.api.comment(selected_post_id, test_string)
        is_comment_present = False
        for comment in self.bot.api.get_media_comments(selected_post_id).json()["comments"]:
            if comment["text"] == test_string:
                is_comment_present = True
                break
        print("Commented on post at 'https://www.instagram.com/p/%s/'"%selected_post_code)
        assert is_comment_present

    def test_get_tags(self):
        assert len(self.bot.get_autocomplete_tags("bitcoin")) > 0