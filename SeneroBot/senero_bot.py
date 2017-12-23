import logging

from InstagramAPI import InstagramAPI


class SeneroBot(object):
    def __init__(self, username, password, tags):
        self.api = InstagramAPI(username, password)
        self.api.login()
        # self.tags = self.get_autocomplete_tags(tags)
        self.tags=tags
        logging.info("Selected tags are: %s" % self.tags)

    def get_relevant_items(self):
        logging.info("Started loading tags...")
        all_relevant_items = []
        for tag in self.tags:
            feed_resp = self.api.get_hashtag_feed(tag)
            items = feed_resp.json()["items"]
            items = SeneroBot.filter_items(items)
            all_relevant_items.extend(items)
        SeneroBot.sort_items_by_likecount(all_relevant_items)
        logging.info("Finished loading tags!")
        return all_relevant_items

    def get_autocomplete_tags(self, tags):
        all_tags = []
        for tag in tags:
            autocomplete_tags = self.api.search_tags(tag).json()["results"]
            try:
                all_tags.extend([autocomplete_tag["name"] for autocomplete_tag in autocomplete_tags][:5])
            except IndexError:
                all_tags.extend([autocomplete_tag["name"] for autocomplete_tag in autocomplete_tags])

        return all_tags

    @staticmethod
    def filter_items(items):
        items = list(filter(lambda item: not item["has_liked"], items))
        return items

    @staticmethod
    def sort_items_by_likecount(items):
        items.sort(key=lambda item: item["like_count"], reverse=True)