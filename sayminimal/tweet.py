#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re
import os
import time
import logging
import pkg_resources
import urllib.parse

import tweepy
from mastodon import Mastodon
import yaml
import gi
gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")
from gi.repository import Gtk, Gdk

# Credentials for this app to use OAuth
# APP_KEY = "9MNMUIprKQBvdH08Ms1w"
# APP_SECRET = "NhPoCBwtVk9P1Tc7Ru3KaYTh5rjF9vUbcmIOS3tH0"

DEFAULT_APP_KEY = "zcoB9FlShIl3GI2BgZLvldEjo"
DEFAULT_APP_SECRET = "tfzg6wnXwhbUReB8C3idgvNuzVSpIwOQFAZublN6ShpavXez2m"

GRUBER_URL_REGEX = re.compile( r'(?i)\b((?:https?:(?:/{1,3}|[a-z0-9%])|[a-z0-9.\-]+[.](?:com|net|org|edu|gov|mil|aero|asia|biz|cat|coop|info|int|jobs|mobi|museum|name|post|pro|tel|travel|xxx|ac|ad|ae|af|ag|ai|al|am|an|ao|aq|ar|as|at|au|aw|ax|az|ba|bb|bd|be|bf|bg|bh|bi|bj|bm|bn|bo|br|bs|bt|bv|bw|by|bz|ca|cc|cd|cf|cg|ch|ci|ck|cl|cm|cn|co|cr|cs|cu|cv|cx|cy|cz|dd|de|dj|dk|dm|do|dz|ec|ee|eg|eh|er|es|et|eu|fi|fj|fk|fm|fo|fr|ga|gb|gd|ge|gf|gg|gh|gi|gl|gm|gn|gp|gq|gr|gs|gt|gu|gw|gy|hk|hm|hn|hr|ht|hu|id|ie|il|im|in|io|iq|ir|is|it|je|jm|jo|jp|ke|kg|kh|ki|km|kn|kp|kr|kw|ky|kz|la|lb|lc|li|lk|lr|ls|lt|lu|lv|ly|ma|mc|md|me|mg|mh|mk|ml|mm|mn|mo|mp|mq|mr|ms|mt|mu|mv|mw|mx|my|mz|na|nc|ne|nf|ng|ni|nl|no|np|nr|nu|nz|om|pa|pe|pf|pg|ph|pk|pl|pm|pn|pr|ps|pt|pw|py|qa|re|ro|rs|ru|rw|sa|sb|sc|sd|se|sg|sh|si|sj|Ja|sk|sl|sm|sn|so|sr|ss|st|su|sv|sx|sy|sz|tc|td|tf|tg|th|tj|tk|tl|tm|tn|to|tp|tr|tt|tv|tw|tz|ua|ug|uk|us|uy|uz|va|vc|ve|vg|vi|vn|vu|wf|ws|ye|yt|yu|za|zm|zw)/)(?:[^\s()<>{}\[\]]+|\([^\s()]*?\([^\s()]+\)[^\s()]*?\)|\([^\s]+?\))+(?:\([^\s()]*?\([^\s()]+\)[^\s()]*?\)|\([^\s]+?\)|[^\s`!()\[\]{};:\'".,<>?«»“”‘’])|(?:(?<!@)[a-z0-9]+(?:[.\-][a-z0-9]+)*[.](?:com|net|org|edu|gov|mil|aero|asia|biz|cat|coop|info|int|jobs|mobi|museum|name|post|pro|tel|travel|xxx|ac|ad|ae|af|ag|ai|al|am|an|ao|aq|ar|as|at|au|aw|ax|az|ba|bb|bd|be|bf|bg|bh|bi|bj|bm|bn|bo|br|bs|bt|bv|bw|by|bz|ca|cc|cd|cf|cg|ch|ci|ck|cl|cm|cn|co|cr|cs|cu|cv|cx|cy|cz|dd|de|dj|dk|dm|do|dz|ec|ee|eg|eh|er|es|et|eu|fi|fj|fk|fm|fo|fr|ga|gb|gd|ge|gf|gg|gh|gi|gl|gm|gn|gp|gq|gr|gs|gt|gu|gw|gy|hk|hm|hn|hr|ht|hu|id|ie|il|im|in|io|iq|ir|is|it|je|jm|jo|jp|ke|kg|kh|ki|km|kn|kp|kr|kw|ky|kz|la|lb|lc|li|lk|lr|ls|lt|lu|lv|ly|ma|mc|md|me|mg|mh|mk|ml|mm|mn|mo|mp|mq|mr|ms|mt|mu|mv|mw|mx|my|mz|na|nc|ne|nf|ng|ni|nl|no|np|nr|nu|nz|om|pa|pe|pf|pg|ph|pk|pl|pm|pn|pr|ps|pt|pw|py|qa|re|ro|rs|ru|rw|sa|sb|sc|sd|se|sg|sh|si|sj|Ja|sk|sl|sm|sn|so|sr|ss|st|su|sv|sx|sy|sz|tc|td|tf|tg|th|tj|tk|tl|tm|tn|to|tp|tr|tt|tv|tw|tz|ua|ug|uk|us|uy|uz|va|vc|ve|vg|vi|vn|vu|wf|ws|ye|yt|yu|za|zm|zw)\b/?(?!@)))' )

URL_LEN_CACHE_TIME = 24*3600

CONF_FILE = "~/.config/sayminimal/conf.yml"
GLADE_FILE = "fusion.glade"

class Conf:
    def __init__(self):
        self.conf_file = os.path.expanduser(CONF_FILE)
        try:
            with open(self.conf_file) as f:
                self.vals = yaml.load(f)
            self.MigrateTo3()
        except FileNotFoundError:
            logging.warning("Couldn't load conf file, opening a new one.")
            self.vals = {}

    def Get(self, key):
        return self.vals[key]

    def Set(self, key, val):
        self.vals[key] = val
        self.Save()

    def Unset(self, key):
        del self.vals[key]
        self.Save()

    def Save(self):
        with open(self.conf_file, "w") as f:
            f.write(yaml.dump(self.vals))

    def MigrateTo3(self):
        if "conf_ver" in self.vals.keys():
            return
        v3 = {"conf_ver": 3}
        for key in ["consumer_key", "consumer_secret", "oauth_key", "oauth_secret"]:
            if key in self.vals.keys():
                v3["twitter_"+key] = self.vals[key]
        self.vals = v3
        self.Save()

class MastodonApi(Mastodon):
    def __init__(self, conf, builder):
        self.conf = conf
        self.builder = builder

        try:
            api_base_url = self.conf.Get("mastodon_instance")
            if api_base_url[-1:] == "/":
                api_base_url = api_base_url[:-1]

        except KeyError:
            api_base_url = self.PickInstance()

        try:
            key = self.conf.Get("mastodon_key")
            secret = self.conf.Get("mastodon_secret")
        except KeyError:
            key, secret = self.RegisterApp(api_base_url)

        try:
            token = self.conf.Get("mastodon_access_token")
            Mastodon.__init__(self,
                client_id=key,
                client_secret=secret,
                access_token=token,
                api_base_url=api_base_url,
            )
        except KeyError:
            token = None
            Mastodon.__init__(self,
                client_id=key,
                client_secret=secret,
                api_base_url=api_base_url,
            )
        if token is None:
            token = self.RequestAuth()
            self.access_token = token
            self.conf.Set("mastodon_access_token", token)

        try:
            self.current_user_id = self.conf.Get("current_user_id")
        except KeyError:
            self.current_user_id = self.account_verify_credentials()["id"]
            self.conf.Set("current_user_id", self.current_user_id)


    def PickInstance(self):
        dialog = self.builder.get_object("instance_dialog")
        instance_entry = self.builder.get_object("instance_entry")
        res = dialog.run()
        if res:
            mastodon_instance = _entry.get_text()
            if "://" not in mastodon_instance:
                # assume we need to add an https:// to it
                mastodon_instance = "https://" + mastodon_instance

            self.conf.Set("mastodon_instance", mastodon_instance)
            return mastodon_instance

        exit("No mastodon instance specified")

    def RegisterApp(self, api_base_url):
        print("api_base_url is '%s'" % api_base_url)
        key, secret = Mastodon.create_app(
            "SayMinimal",
            scopes=["read", "write"],
            api_base_url=api_base_url
        )
        self.conf.Set("mastodon_key", key)
        self.conf.Set("mastodon_secret", secret)
        return key, secret

    def RequestAuth(self):
        authurl = self.auth_request_url(scopes=["read","write"])
        dialog = self.builder.get_object("pin_dialog")
        urlbutton = self.builder.get_object("pin_auth_url")
        urlbutton.set_label(authurl)
        urlbutton.set_uri(authurl)
        res = dialog.run()
        if res:
            pin_field = self.builder.get_object("pin_entry")
            pin = pin_field.get_text()
            dialog.destroy()
            self.conf.Set("mastodon_auth_code", pin)
            if pin:
                token = self.log_in(code=pin, scopes=["read","write"])
                return token
        Gtk.main_quit()
        exit("Can't connect to Mastodon instance without authorization.")

    def CalcStatusLength(self, text):
        return len(text)

class TwitterApi(tweepy.API):
    def __init__(self, conf, builder):
        #Get a twitter API
        self.conf = conf
        self.builder = builder

        try:
            consumer_key = self.conf.Get("twitter_consumer_key")
            consumer_secret = self.conf.Get("twitter_consumer_secret")
        except KeyError:
            consumer_key, consumer_secret = self.GetAppKeys()
            self.conf.Set("twitter_consumer_key", consumer_key)
            self.conf.Set("twitter_consumer_secret", consumer_secret)

        auth = tweepy.OAuthHandler(consumer_key, consumer_secret)

        #If we have the user's OAuth key & secret, we're done. Otherwise,
        #  do the OAuth Dance
        try:
            user_key = self.conf.Get("twitter_oauth_key")
            user_secret = self.conf.Get("twitter_oauth_secret")
            auth.set_access_token(user_key, user_secret)
        except KeyError:
            try:
                pin = self.GetPIN(auth)
            except tweepy.error.TweepError:
                logging.warning("Get authorization URL failed; maybe consumer key is bad?")
                self.conf.Unset("twitter_consumer_key")
                self.conf.Unset("twitter_consumer_secret")
                exit(1)

            auth.get_access_token(pin)
            self.conf.Set("twitter_oauth_key", auth.access_token)
            self.conf.Set("twitter_oauth_secret", auth.access_token_secret)

        tweepy.API.__init__(self, auth)

    def GetUrlLen(self):
        try:
            assert int(time.time()) < int(self.conf.Get("tco_url_len_timestamp")) + URL_LEN_CACHE_TIME
            return int(self.conf.Get("tco_url_len"))
        except (KeyError, AssertionError):
            url_len = self.configuration()["short_url_length"]
            self.conf.Set("tco_url_len", url_len)
            self.conf.Set("tco_url_len_timestamp", int(time.time()))
            return url_len


    def GetAppKeys(self):
        dialog = self.builder.get_object("consumerkey_dialog")
        res = dialog.run()
        dialog.destroy()
        if res: # User clicked "Register an App" button
            dialog2 = self.builder.get_object("consumerkey_entry_dialog")
            res2 = dialog2.run()
            if res2:
                consumer_key = self.builder.get_object("consumer_key_entry").get_text()
                consumer_secret = self.builder.get_object("consumer_secret_entry").get_text()
                dialog2.destroy()
                return (consumer_key, consumer_secret)
            else:
                logging.warning("User canceled consumer key entry")

        logging.warning("Using default Consumer Key")
        return (DEFAULT_APP_KEY, DEFAULT_APP_SECRET)

    def GetPIN(self, auth):
        authurl = auth.get_authorization_url()
        dialog = self.builder.get_object("pin_dialog")
        urlbutton = self.builder.get_object("pin_auth_url")
        urlbutton.set_label(authurl)
        urlbutton.set_uri(authurl)
        res = dialog.run()
        if res:
            pin_field = self.builder.get_object("pin_entry")
            pin = pin_field.get_text()
            dialog.destroy()
            if pin:
                return pin
        Gtk.main_quit()
        exit("Can't connect to Twitter without authorization.")

    def CalcStatusLength(self, text):
        url_len_str = self.GetUrlLen()*" "
        n = len(GRUBER_URL_REGEX.sub(url_len_str, text))
        return n


class StatusWindow:
    def __init__(self, builder, conf, twitter=True, mastodon=True):

        if twitter:
            self.twitter = TwitterApi(conf, builder)
        else:
            self.twitter = None
        print("Done initializing TwitterApi")

        if mastodon:
            self.mastodon = MastodonApi(conf, builder)
        else:
            self.mastodon = None
        print("Done initializing MastodonApi")

        self.attached_media = None

        self.threaded = False
        self.twitter_reply_id = None
        self.twitter_reply_text = ""
        self.mastodon_reply_id = None
        self.mastodon_reply_text = ""

        self.window = builder.get_object('status_window')
        self.label = builder.get_object('prompt_label')
        self.chars_label = builder.get_object('status_chars')
        self.bonus_label = builder.get_object('bonus_label')
        self.textbox = builder.get_object('status_entry')

        #Events
        self.window.connect("delete-event", Gtk.main_quit)
        self.window.connect("key-press-event", self.keypress)
        self.textbox.connect("changed", self.text_changed)
        self.textbox.connect("activate", self.submit_status)

        print("About to show_all()")
        #Start
        self.window.show_all()
        self.text_changed(self.textbox)
        Gtk.main()

    def text_changed(self, entry):
        text = entry.get_text()
        lbl = ""
        if self.twitter:
            lbl += "(%d / 280) " % self.twitter.CalcStatusLength(text)
        if self.mastodon:
            lbl += "(%d / 500) " % self.mastodon.CalcStatusLength(text)

        self.chars_label.set_text(lbl)

        # labeltext = re.sub(r"\(-?[0-9]+\)", "("+str(140-n)+")", labeltext)
        #self.label.set_text(labeltext)

    def keypress(self, widget, event):
        key_name = Gdk.keyval_name(event.keyval)
        if event.state & Gdk.ModifierType.SHIFT_MASK and key_name == "Return":
            self.textbox.do_insert_at_cursor(self.textbox, "\n")
        elif (event.state & Gdk.ModifierType.MOD1_MASK) and key_name == "i":
            self.prompt_for_media_file()
        elif (event.state & Gdk.ModifierType.MOD1_MASK) and key_name == "t":
            self.toggle_threaded()
        elif event.keyval == Gdk.KEY_Escape:
            Gtk.main_quit()

    def toggle_threaded(self):
        if not self.threaded:
            if self.twitter:
                recent_tweets = self.twitter.user_timeline(count=1)
                if not len(recent_tweets):
                    logging.warning("Can't find previous tweets to thread to.")
                else:
                    #print(recent_tweet[0])
                    self.twitter_reply_id = recent_tweets[0].id
                    self.twitter_reply_text = recent_tweets[0].text
            if self.mastodon:
                user_id = self.mastodon.current_user_id
                recent_toots = self.mastodon.account_statuses(user_id, limit=1)
                if not len(recent_toots):
                    logging.warning("Can't find previous toot to thread to.")
                else:
                    self.mastodon_reply_id = recent_toots[0]["id"]
                    self.mastodon_reply_text = recent_toots[0]["content"] # FF: maybe convert this from HTML?

        else:
            self.threaded = False
            self.twitter_reply_id = None
            self.twitter_reply_text = ""
            self.mastodon_reply_id = None
            self.mastodon_reply_text = ""

        self.update_bonus_label()

    def prompt_for_media_file(self):
        fd = Gtk.FileChooserDialog(title="Select a file to upload...",
                                   parent=self.window,
                                   action=Gtk.FileChooserAction.OPEN,
                                   buttons=(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
                                   Gtk.STOCK_OPEN, Gtk.ResponseType.OK))
        response = fd.run()
        if response == Gtk.ResponseType.OK:
            image_file = fd.get_filename()
            if not self.attached_media:
                labeltext = self.label.get_text()
                self.label.set_text(labeltext + " (Image attached)")
            self.attached_media = image_file
            self.update_bonus_label()
        fd.destroy()

    def update_bonus_label(self):
        s = ""
        if self.attached_media:
            s += "Attached: %s\n" % self.attached_media
        if self.twitter_reply_id:
            s += "(Twitter) Replying to: %s\n> %s\n\n" % (
                self.twitter_reply_id,
                self.twitter_reply_text,)
        if self.mastodon_reply_id:
            s += "(Mastodon) Replying to: %s\n> %s\n\n" % (
                self.mastodon_reply_id,
                self.mastodon_reply_text,
            )
        self.bonus_label.set_label(s)

    def display_error(self, e):
        dlg = Gtk.MessageDialog(self.window, Gtk.DialogFlags.DESTROY_WITH_PARENT | Gtk.DialogFlags.MODAL,
             Gtk.MessageType.ERROR, Gtk.ButtonsType.CLOSE, str(e))
        dlg.run()
        dlg.destroy()

    def submit_status(self, entry):
        text = entry.get_text()
        if not text: return

        entry.set_sensitive(False)
        if self.twitter:
            self.submit_tweet(text)
        if self.mastodon:
            self.submit_toot(text)
        Gtk.main_quit()

    def submit_toot(self, text):
        media_ids = None
        if self.attached_media:
            self.label.set_text("Uploading image...")
            media = self.mastodon.media_post(self.attached_media)
            media_ids = [media["id"]]

        self.mastodon.status_post(text,
            in_reply_to_id=self.mastodon_reply_id, # Can be None, & that's OK.
            media_ids=media_ids,
        )


    def submit_tweet(self, text):
        if self.attached_media and not self.twitter_reply_id:
            self.label.set_text("Uploading image and message...")
            try:
                self.twitter.update_with_media(self.attached_media, status=text)
            except Exception as e:
                self.display_error(e)

        elif self.attached_media and self.twitter_reply_id:
            self.label.set_text("Uploading image and reply...")
            try:
                self.twitter.update_with_media(self.attached_media, status=text,
                    in_reply_to_status_id=self.twitter_reply_id)
            except Exception as e:
                self.display_error(e)

        elif self.twitter_reply_id:
            self.label.set_text("Sending reply...")
            try:
                self.twitter.update_status(text, in_reply_to_status_id=self.twitter_reply_id)
            except Exception as e:
                self.display_error(e)

        else:
            self.label.set_text("Sending message...")
            try:
                self.twitter.update_status(text)
            except Exception as e:
                self.display_error(e)


def main():
    conf = Conf()
    builder = Gtk.Builder()
    if __name__ == "__main__": # Testing
        builder.add_from_file(GLADE_FILE)
    else: # Installed with pip, probably
        builder.add_from_string(
            pkg_resources.resource_string(__name__, GLADE_FILE).decode('utf-8')
        )
    StatusWindow(builder, conf=conf)

if __name__ == "__main__":
    main()
