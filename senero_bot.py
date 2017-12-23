import logging
from time import sleep

import yaml

from InstagramAPI import InstagramAPI
from SeneroBot.senero_bot import SeneroBot

SLEEP_INTERVAL = 5.0
logging.basicConfig(level=logging.INFO, format="%(levelname)s at %(asctime)s: %(message)s")

if __name__ == '__main__':
    with open("config.yaml") as conf_file:
        config = yaml.load(conf_file)
    with open("comment.txt") as comment_file:
        comment_text = comment_file.read()

    bot = SeneroBot(config["bot_creds"]["username"], config["bot_creds"]["password"], config["tags_to_search"])
    items = bot.get_relevant_items()
    while True:
        try:
            for media_code, media_id in zip(InstagramAPI.extract_media_codes_from_items(items),
                                            InstagramAPI.extract_media_ids_from_items(items)):
                if not bot.api.is_user_commented(media_id):
                    bot.api.like(media_id)
                    bot.api.comment(media_id, comment_text)
                    logging.info("Commented on a post at 'https://www.instagram.com/p/%s/'" % media_code)
                    sleep(SLEEP_INTERVAL)
        except Exception as e:
            logging.exception(str(e))
