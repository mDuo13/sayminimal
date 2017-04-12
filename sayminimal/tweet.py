#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re
import os
import logging
import pkg_resources

import tweepy
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

URL_LEN_STR = 25*" " #t.co automatically shortens URLs to this length.
#Technically we're supposed to lookup & cache this daily instead of hardcoding it.

CONF_FILE = "~/.config/sayminimal/conf.yml"
GLADE_FILE = "twitters.glade"

class Conf:
    def __init__(self):
        self.conf_file = os.path.expanduser(CONF_FILE)
        try:
            with open(self.conf_file) as f:
                self.vals = yaml.load(f)
        except FileNotFoundError:
            logging.warning("Couldn't load conf file, opening a new one.")
            self.vals = {}

    def Get(self, key):
        return self.vals[key]

    def Set(self, key, val):
        self.vals[key] = val
        with open(self.conf_file, "w") as f:
            f.write(yaml.dump(self.vals))

    def Unset(self, key):
        del self.vals[key]
        with open(self.conf_file, "w") as f:
            f.write(yaml.dump(self.vals))



class AuthedApi(tweepy.API):
    def __init__(self, conf, builder):
        #Get a twitter API
        self.conf = conf
        self.builder = builder

        try:
            consumer_key = self.conf.Get("consumer_key")
            consumer_secret = self.conf.Get("consumer_secret")
        except KeyError:
            consumer_key, consumer_secret = self.GetAppKeys()
            self.conf.Set("consumer_key", consumer_key)
            self.conf.Set("consumer_secret", consumer_secret)

        auth = tweepy.OAuthHandler(consumer_key, consumer_secret)

        #If we have the user's OAuth key & secret, we're done. Otherwise,
        #  do the OAuth Dance
        try:
            user_key = self.conf.Get("oauth_key")
            user_secret = self.conf.Get("oauth_secret")
            auth.set_access_token(user_key, user_secret)
        except KeyError:
            try:
                pin = self.GetPIN(auth)
            except tweepy.error.TweepError:
                logging.warning("Get authorization URL failed; maybe consumer key is bad?")
                self.conf.Unset("consumer_key")
                self.conf.Unset("consumer_secret")
                exit(1)

            auth.get_access_token(pin)
            self.conf.Set("oauth_key", auth.access_token)
            self.conf.Set("oauth_secret", auth.access_token_secret)

        tweepy.API.__init__(self, auth)

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


class TweetWindow:
    def __init__(self, builder):

        self.api = AuthedApi(Conf(), builder)
        self.attached_media = None
        self.reply_id = None

        self.window = builder.get_object('tweetwin')
        self.label = builder.get_object('tweetprompt')
        self.bonus_label = builder.get_object('bonus_label')
        self.textbox = builder.get_object('tweetentry')

        #Events
        self.window.connect("delete-event", Gtk.main_quit)
        self.window.connect("key-press-event", self.keypress)
        self.textbox.connect("changed", self.text_changed)
        self.textbox.connect("activate", self.enter_tweet)

        #Start
        self.window.show_all()
        Gtk.main()

    def text_changed(self, entry):
        #n = entry.get_text_length()
        text = entry.get_text()
        n = len(GRUBER_URL_REGEX.sub(URL_LEN_STR, text))
        labeltext = self.label.get_text()
        labeltext = re.sub(r"\(-?[0-9]+\)", "("+str(140-n)+")", labeltext)
        self.label.set_text(labeltext)

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
        if self.reply_id == None:
            recent_tweet = self.api.user_timeline(count=1)
            if not len(recent_tweet):
                logging.warning("Can't find previous tweets to thread to.")
                return
            #print(recent_tweet[0])
            self.reply_id = recent_tweet[0].id
            self.reply_text = recent_tweet[0].text
        else:
            self.reply_id = None
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
        if self.reply_id:
            s += "Replying to: %s\n> %s" % (self.reply_id, self.reply_text)
        self.bonus_label.set_label(s)

    def display_error(self, e):
        dlg = Gtk.MessageDialog(self.window, Gtk.DialogFlags.DESTROY_WITH_PARENT | Gtk.DialogFlags.MODAL,
             Gtk.MessageType.ERROR, Gtk.ButtonsType.CLOSE, str(e))
        dlg.run()
        dlg.destroy()

    def enter_tweet(self, entry):
        text = entry.get_text()
        if text:
            entry.set_sensitive(False)

            if self.attached_media and not self.reply_id:
                self.label.set_text("Uploading image and message to Twitter...")
                try:
                    self.api.update_with_media(self.attached_media, status=text)
                except Exception as e:
                    self.display_error(e)

            elif self.attached_media and self.reply_id:
                self.label.set_text("Uploading image and reply to Twitter...")
                try:
                    self.api.update_with_media(self.attached_media, status=text,
                        in_reply_to_status_id=self.reply_id)
                except Exception as e:
                    self.display_error(e)

            elif self.reply_id:
                self.label.set_text("Sending reply to Twitter...")
                try:
                    self.api.update_status(text, in_reply_to_status_id=self.reply_id)
                except Exception as e:
                    self.display_error(e)

            else:
                self.label.set_text("Sending message to Twitter...")
                try:
                    self.api.update_status(text)
                except Exception as e:
                    self.display_error(e)

            Gtk.main_quit()

def main():
    #Initialize from glade
    builder = Gtk.Builder()
    #builder.add_from_file(GLADE_FILE)
    builder.add_from_string(
        pkg_resources.resource_string(__name__, GLADE_FILE).decode('utf-8')
    )
    TweetWindow(builder)

if __name__ == "__main__":
    main()
