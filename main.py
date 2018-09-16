from tweepy.streaming import StreamListener
from tweepy import OAuthHandler, Stream
from tweepy.api import API
from discord import Webhook, RequestsWebhookAdapter, Embed
from time import gmtime, strftime
from time import sleep
import discord
import random
import json
import datetime
import html
import re
from config import data_json
import urllib3


class StdOutListener(StreamListener):
    def __init__(self, api=None):
        self.api = api or API()

        self.data_d = data_json['Discord']

    def _on_status(self, status):
        colors = [0x7f0000, 0x40d9ff, 0x8c7399, 0xd97b6c, 0xf2ff40, 0x8fb6bf, 0x502d59, 0x00aaff, 0xd600e6, 0x401100, 0xff00aa, 0xff8c40, 0x17330d,
                  0x0066bf, 0x33001b, 0xb39886, 0x163a59, 0x8c235b, 0x8c5e00, 0x000c59,
                  0xffbfd9, 0x3d3df2, 0x590018, 0xf2c200, 0xc8bfff, 0xf23d6d,
                  0xd9c36c, 0xb380ff, 0xff0022, 0x7c29a6]

        data = status._json

        for data_discord in self.data_d:
            if data['user']['id_str'] not in data_discord['twitter_ids']:
                worth_posting = False
                if 'IncludeReplyToUser' in data_discord:  # other Twitter user tweeting to your followed Twitter user
                    if data_discord['IncludeReplyToUser']:
                        if data['in_reply_to_user_id_str'] in data_discord['twitter_ids']:
                            worth_posting = True
            else:
                worth_posting = True
                # your followed Twitter users tweeting to random Twitter users
                # (relevant if you only want status updates/opt out of conversations)
                if 'IncludeUserReply' in data_discord:
                    if not data_discord['IncludeUserReply'] and data['in_reply_to_user_id'] is not None:
                            worth_posting = False

            if 'IncludeRetweet' in data_discord:  # retweets...
                if not data_discord['IncludeRetweet']:
                    if 'retweeted_status' in data:
                        worth_posting = False  # retweet

            if not worth_posting:
                continue

            for wh_url in data_discord['webhook_urls']:
                username = data['user']['screen_name']
                icon_url = data['user']['profile_image_url']

                text = ''
                if 'extended_tweet' in data:
                    text = data['extended_tweet']['full_text']
                else:
                    text = data['text']

                for url in data['entities']['urls']:
                    if url['expanded_url'] is None:
                        continue
                    text = text.replace(url['url'], "[%s](%s)" %(url['display_url'],url['expanded_url']))

                for userMention in data['entities']['user_mentions']:
                    text = text.replace('@%s' % userMention['screen_name'],
                                        '[@%s](https://twitter.com/%s)' % (userMention['screen_name'],
                                                                           userMention['screen_name']))


                media_url = ''
                media_type = ''
                if 'extended_tweet' in data:
                    for hashtag in sorted(data['extended_tweet']['entities']["hashtags"], key=lambda k: k["text"],
                                          reverse=True):
                        text = text.replace('#%s' % hashtag['text'],
                                            '[#%s](https://twitter.com/hashtag/%s)' % (hashtag['text'],
                                                                                       hashtag['text']))
                    
                    if 'media' in data['extended_tweet']['entities']:
                        for media in data['extended_tweet']['entities']['media']:
                            if media['type'] == 'photo':
                                media_url = media['media_url']
                                
                for hashtag in sorted(data['entities']["hashtags"], key=lambda k: k["text"],
                                      reverse=True):
                    text = text.replace('#%s' % hashtag['text'],
                                        '[#%s](https://twitter.com/hashtag/%s)' % (hashtag['text'],
                                                                                   hashtag['text']))
                                

                if 'media' in data['entities']:
                    for media in data['entities']['media']:
                        if media['type'] == 'photo' and not media_url:
                            media_url = media['media_url_https']
                            media_type = 'photo'
                        if media['type'] == 'video':
                            media_url = media['media_url_https']
                            media_type = 'photo'
                        if media['type'] == 'animated_gif' and media_type != "video":
                            media_url = media['media_url_https']
                            media_type = 'photo'

                video_alert = False

                if 'extended_entities' in data and 'media' in data['extended_entities']:
                    for media in data['extended_entities']['media']:
                        if media['type'] == 'photo' and not media_url:
                            media_url = media['media_url_https']
                            media_type = media['type']
                        if media['type'] == 'video':
                            video_alert = True
                            media_type = media['type']
                        if media['type'] == 'animated_gif' and media_type != "video":
                            video_alert = True
                            media_type = 'gif'

                if video_alert:
                    text += " **[tweet has gif/video]**"

                text = html.unescape(text)

                embed = Embed(colour=random.choice(colors),
                              url='https://twitter.com/{}/status/{}'.format(data['user']['screen_name'],
                                                                            data['id_str']),
                              title=data['user']['name'],
                              description=text,
                              timestamp=datetime.datetime.strptime(data['created_at'], '%a %b %d %H:%M:%S +0000 %Y'))

                embed.set_author(name=username,
                                 url="https://twitter.com/" + data['user']['screen_name'],
                                 icon_url=icon_url)
                embed.set_footer(text='Tweeted',
                                 icon_url='https://cdn1.iconfinder.com/data/icons/iconza-circle-social/64/697029-twitter-512.png')

                if media_url:
                    embed.set_image(url=media_url)

                print(strftime("[%Y-%m-%d %H:%M:%S]", gmtime()), data['user']['screen_name'], 'twittered.')

                if 'quoted_status' in data:
                    text = data['quoted_status']['text']
                    for url in data['quoted_status']['entities']['urls']:
                        if url['expanded_url'] is None:
                            continue
                        text = text.replace(url['url'], "[%s](%s)" % (url['display_url'], url['expanded_url']))

                    for userMention in data['quoted_status']['entities']['user_mentions']:
                        text = text.replace('@%s' % userMention['screen_name'],
                                            '[@%s](https://twitter.com/%s)' % (userMention['screen_name'],
                                                                               userMention['screen_name']))

                    for hashtag in sorted(data['entities']["hashtags"], key=lambda k: k["text"], reverse=True):
                        text = text.replace('#%s' % hashtag['text'],
                                            '[#%s](https://twitter.com/hashtag/%s)' % (hashtag['text'],
                                                                                       hashtag['text']))

                    text = html.unescape(text)

                    embed.add_field(name=data['quoted_status']['user']['screen_name'], value=text)

                regex = r"discordapp\.com\/api\/webhooks\/(?P<id>\d+)\/(?P<token>.+)"
                match = re.search(regex, wh_url)

                if match:
                    webhook = Webhook.partial(match.group("id"), match.group("token"), adapter=RequestsWebhookAdapter())
                    try:
                        if data_discord["Filtered_Text"]: # if Filtered_Text is present do the filtering
                            if any(Filtered_Text in text for Filtered_Text in data_discord["Filtered_Text"]):
                                webhook.send(embed=embed)
                            else: #Filtered_Text was not present, always post.
                                webhook.send(embed=embed)
                    except discord.errors.HTTPException as error:
                        print('---------Error---------')
                        print('discord.errors.HTTPException')
                        print("You've found an error. Please contact the owner (https://discord.gg/JV5eUB) "
                              "and send him what follows below:")
                        print(error)
                        print(data)
                        print('-----------------------')

    def on_status(self, status):
        """Called when a new status arrives"""
        try:
            self._on_status(status)
        except Exception as error:
           print('---------Error---------')
           print('unknown error')
           print("You've found an error. Please contact the owner (https://discord.gg/JV5eUB) "
                 "and send him what follows below:")
           print(error)
           print(status)
           print('-----------------------')

    def on_limit(self, track):
        """Called when a limitation notice arrives"""
        print('on_limit')
        print(track)
        return

    def on_error(self, status_code):
        """Called when a non-200 status code is returned"""
        print('on_error')
        print(status_code)
        return False

    def on_disconnect(self, notice):
        """Called when twitter sends a disconnect notice
        Disconnect codes are listed here:
        https://dev.twitter.com/docs/streaming-apis/messages#Disconnect_messages_disconnect
        """
        print('on_disconnect')
        print(notice)
        return

    def on_warning(self, notice):
        """Called when a disconnection warning message arrives"""
        print('on_warning')
        print(notice)
        return

if __name__ == '__main__':
    print('Bot started.')

    data_json['twitter_ids'] = []
    for element in data_json['Discord']:
        data_json['twitter_ids'].extend(x for x in element['twitter_ids'] if x not in data_json['twitter_ids'])

    print('{} Twitter users are being followed.'.format(len(data_json['twitter_ids'])))

    l = StdOutListener()
    auth = OAuthHandler(data_json['Twitter']['consumer_key'], data_json['Twitter']['consumer_secret'])
    auth.set_access_token(data_json['Twitter']['access_token'], data_json['Twitter']['access_token_secret'])
    stream = Stream(auth, l)

    print('Twitter stream started.')
    
    while True:
        try:
            stream.filter(follow=data_json['twitter_ids'])
        except urllib3.exceptions.ProtocolError as error:
            print('---------Error---------')
            print('This is probably caused by "Connection reset by peer." Ignore. Nothing you can do.')
            print(error)
            print('Sleeping for 10 seconds then continuing.')
            sleep(10)
            print('Twitter streaming continues.')
            print('-----------------------')
        except ConnectionResetError as error:
            print('---------Error---------')
            print('This is probably caused by "Connection reset by peer." Ignore. Nothing you can do.')
            print(error)
            print('Sleeping for 10 seconds then continuing.')
            sleep(10)
            print('Twitter streaming continues.')
            print('-----------------------')
        except Exception as error:
            print('---------Error---------')
            print('unknown error')
            print("You've found an error. Please contact the owner (https://discord.gg/JV5eUB) "
                  "and send him what follows below:")
            print(error)
            print(data_json)
            print('-----------------------')
            break
