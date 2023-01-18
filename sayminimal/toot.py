#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re
import os
import time
import logging
import pkg_resources
import urllib.parse
import html

from mastodon import Mastodon
import yaml
import gi
gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")
from gi.repository import Gtk, Gdk, GdkPixbuf


# Currently unused, but could use again for purposes of calculating adjusted toot lengths after link shortening:
GRUBER_URL_REGEX = re.compile( r'(?i)\b((?:https?:(?:/{1,3}|[a-z0-9%])|[a-z0-9.\-]+[.](?:com|net|org|edu|gov|mil|aero|asia|biz|cat|coop|info|int|jobs|mobi|museum|name|post|pro|tel|travel|xxx|ac|ad|ae|af|ag|ai|al|am|an|ao|aq|ar|as|at|au|aw|ax|az|ba|bb|bd|be|bf|bg|bh|bi|bj|bm|bn|bo|br|bs|bt|bv|bw|by|bz|ca|cc|cd|cf|cg|ch|ci|ck|cl|cm|cn|co|cr|cs|cu|cv|cx|cy|cz|dd|de|dj|dk|dm|do|dz|ec|ee|eg|eh|er|es|et|eu|fi|fj|fk|fm|fo|fr|ga|gb|gd|ge|gf|gg|gh|gi|gl|gm|gn|gp|gq|gr|gs|gt|gu|gw|gy|hk|hm|hn|hr|ht|hu|id|ie|il|im|in|io|iq|ir|is|it|je|jm|jo|jp|ke|kg|kh|ki|km|kn|kp|kr|kw|ky|kz|la|lb|lc|li|lk|lr|ls|lt|lu|lv|ly|ma|mc|md|me|mg|mh|mk|ml|mm|mn|mo|mp|mq|mr|ms|mt|mu|mv|mw|mx|my|mz|na|nc|ne|nf|ng|ni|nl|no|np|nr|nu|nz|om|pa|pe|pf|pg|ph|pk|pl|pm|pn|pr|ps|pt|pw|py|qa|re|ro|rs|ru|rw|sa|sb|sc|sd|se|sg|sh|si|sj|Ja|sk|sl|sm|sn|so|sr|ss|st|su|sv|sx|sy|sz|tc|td|tf|tg|th|tj|tk|tl|tm|tn|to|tp|tr|tt|tv|tw|tz|ua|ug|uk|us|uy|uz|va|vc|ve|vg|vi|vn|vu|wf|ws|ye|yt|yu|za|zm|zw)/)(?:[^\s()<>{}\[\]]+|\([^\s()]*?\([^\s()]+\)[^\s()]*?\)|\([^\s]+?\))+(?:\([^\s()]*?\([^\s()]+\)[^\s()]*?\)|\([^\s]+?\)|[^\s`!()\[\]{};:\'".,<>?«»“”‘’])|(?:(?<!@)[a-z0-9]+(?:[.\-][a-z0-9]+)*[.](?:com|net|org|edu|gov|mil|aero|asia|biz|cat|coop|info|int|jobs|mobi|museum|name|post|pro|tel|travel|xxx|ac|ad|ae|af|ag|ai|al|am|an|ao|aq|ar|as|at|au|aw|ax|az|ba|bb|bd|be|bf|bg|bh|bi|bj|bm|bn|bo|br|bs|bt|bv|bw|by|bz|ca|cc|cd|cf|cg|ch|ci|ck|cl|cm|cn|co|cr|cs|cu|cv|cx|cy|cz|dd|de|dj|dk|dm|do|dz|ec|ee|eg|eh|er|es|et|eu|fi|fj|fk|fm|fo|fr|ga|gb|gd|ge|gf|gg|gh|gi|gl|gm|gn|gp|gq|gr|gs|gt|gu|gw|gy|hk|hm|hn|hr|ht|hu|id|ie|il|im|in|io|iq|ir|is|it|je|jm|jo|jp|ke|kg|kh|ki|km|kn|kp|kr|kw|ky|kz|la|lb|lc|li|lk|lr|ls|lt|lu|lv|ly|ma|mc|md|me|mg|mh|mk|ml|mm|mn|mo|mp|mq|mr|ms|mt|mu|mv|mw|mx|my|mz|na|nc|ne|nf|ng|ni|nl|no|np|nr|nu|nz|om|pa|pe|pf|pg|ph|pk|pl|pm|pn|pr|ps|pt|pw|py|qa|re|ro|rs|ru|rw|sa|sb|sc|sd|se|sg|sh|si|sj|Ja|sk|sl|sm|sn|so|sr|ss|st|su|sv|sx|sy|sz|tc|td|tf|tg|th|tj|tk|tl|tm|tn|to|tp|tr|tt|tv|tw|tz|ua|ug|uk|us|uy|uz|va|vc|ve|vg|vi|vn|vu|wf|ws|ye|yt|yu|za|zm|zw)\b/?(?!@)))' )

URL_LEN_CACHE_TIME = 24*3600

CONF_FILE = "~/.config/sayminimal/conf.yml"
GLADE_FILE = "v4.glade"

# Simple stdlib HTML stripping so that threading can show plaintext toot.
# https://stackoverflow.com/a/925630/17380954
from io import StringIO
from html.parser import HTMLParser

class MLStripper(HTMLParser):
    def __init__(self):
        super().__init__()
        self.reset()
        self.strict = False
        self.convert_charrefs= True
        self.text = StringIO()
    def handle_data(self, d):
        self.text.write(d)
    def get_data(self):
        return self.text.getvalue()

def strip_tags(html):
    s = MLStripper()
    s.feed(html)
    return s.get_data()
# End stackoverflow copypasta

class Conf:
    def __init__(self):
        self.conf_file = os.path.expanduser(CONF_FILE)
        try:
            with open(self.conf_file) as f:
                self.vals = yaml.load(f, Loader=yaml.SafeLoader)
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

class MastodonApi(Mastodon):
    def __init__(self, conf, builder):
        self.conf = conf
        self.builder = builder
        self.maxtoot = None

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
            mastodon_instance = instance_entry.get_text()
            if "://" not in mastodon_instance:
                # assume we need to add an https:// to it
                mastodon_instance = "https://" + mastodon_instance

            self.conf.Set("mastodon_instance", mastodon_instance)
            dialog.destroy()
            return mastodon_instance

        exit("No mastodon instance specified")

    def RegisterApp(self, api_base_url):
        logging.debug("api_base_url is '%s'" % api_base_url)
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
        # In practice Mastodon only counts URLs as something like 23 chars each
        # rather than their full length, but this is advisory anyway so /shrug
        return len(text)
    
    def GetMaxTootLen(self):
        if self.maxtoot == None: # Don't have it cached, look it up (kinda slow)
            try:
                # Works on current Mastodon, not older instances or non-Mastodon Fediverse stuff
                self.maxtoot = self.instance().configuration.statuses.max_characters
            except:
                self.maxtoot = "???"
        return self.maxtoot

# https://stackoverflow.com/a/58541701/17380954
def get_textview_contents(textview):
    """Return the contents of a Gtk.TextView widget as a string"""
    buffer = textview.get_buffer()
    startIter, endIter = buffer.get_bounds()    
    text = buffer.get_text(startIter, endIter, False) 
    return text

class StatusWindow:
    def __init__(self, builder, conf):

        self.mastodon = MastodonApi(conf, builder)
        logging.debug("Done initializing MastodonApi")

        self.attached_media = None

        self.mastodon_reply_id = None

        self.window = builder.get_object('status_window')
        self.label = builder.get_object('prompt_label')
        self.chars_label = builder.get_object('status_chars')
        self.thread_label = builder.get_object('thread_label')
        self.thread_toggle = builder.get_object('threaded')
        self.cw_toggle = builder.get_object('cw_toggle')
        self.cw_entry = builder.get_object('cw_entry')
        self.img_button = builder.get_object('img_button')
        self.textbox = builder.get_object('status_entry')

        self.img_dialog = builder.get_object("img_dialog")
        self.img_chooser = builder.get_object('img_chooser')
        self.img_preview = builder.get_object('img_preview')
        self.reset_img_preview()
        self.img_chooser.set_preview_widget(self.img_preview)
        self.alt_text = builder.get_object('alt_text')

        #Events
        self.window.connect("delete-event", Gtk.main_quit)
        self.window.connect("key-press-event", self.keypress)
        self.textbox.connect("changed", self.text_changed)
        self.textbox.connect("activate", self.submit_status)
        self.thread_toggle.connect("toggled", self.toggle_threaded)
        self.img_button.connect("clicked", self.open_image_dialog)
        self.img_chooser.connect("file-set", self.update_img_preview)

        self.cw_toggle.connect("toggled", self.toggle_cw)

        #Start
        self.window.show_all()
        self.text_changed(self.textbox)
        Gtk.main()

    def text_changed(self, entry):
        text = entry.get_text()
        lbl = ""
        if self.mastodon:
            lbl += "(%d / %s) " % (
                self.mastodon.CalcStatusLength(text),
                self.mastodon.GetMaxTootLen(),
            )

        self.chars_label.set_text(lbl)

    def keypress(self, widget, event):
        key_name = Gdk.keyval_name(event.keyval)
        if event.state & Gdk.ModifierType.SHIFT_MASK and key_name == "Return":
            self.textbox.do_insert_at_cursor(self.textbox, "\n")
        elif (event.state & Gdk.ModifierType.MOD1_MASK) and key_name == "i":
            self.open_image_dialog()
        elif (event.state & Gdk.ModifierType.MOD1_MASK) and key_name == "t":
            self.toggle_threaded()
        elif (event.state & Gdk.ModifierType.MOD1_MASK) and key_name == "c":
            self.toggle_cw()
        elif event.keyval == Gdk.KEY_Escape:
            Gtk.main_quit()
    
    def toggle_cw(self, widget=None):
        cw_on = self.cw_toggle.get_active()
        if widget == None:
            # Called through keyboard shortcut, update the UI.
            cw_on = not cw_on
            self.cw_toggle.set_active(cw_on)

        if cw_on:
            self.cw_entry.show()
        else:
            self.cw_entry.hide()
            self.window.resize(600, 40) # shrink back

    def toggle_threaded(self, widget=None):
        thread_on = self.thread_toggle.get_active()
        if widget == None:
            # Called through keyboard shortcut, update the UI.
            thread_on = not thread_on
            self.thread_toggle.set_active(thread_on)

        if thread_on:
            self.thread_label.show()
            user_id = self.mastodon.current_user_id
            recent_toots = self.mastodon.account_statuses(user_id, limit=1)
            if not len(recent_toots):
                logging.warning("Can't find previous toot to thread to.")
                self.thread_toggle.set_active(False)
            else:
                self.mastodon_reply_id = recent_toots[0]["id"]

                html_reply = recent_toots[0]["content"]
                # Alternative version using bleach to strip HTML tags:
                #text_reply = html.unescape(bleach.clean(html_reply, tags=[], strip=True))
                text_reply = html.unescape(strip_tags(html_reply))
                self.thread_label.set_label( "Replying to: %s\n> %s\n\n" % (
                    self.mastodon_reply_id,
                    text_reply,
                ))

        else:
            self.mastodon_reply_id = None
            self.thread_label.set_label("")
            self.thread_label.hide()
            self.window.resize(600, 40) # shrink back

    def open_image_dialog(self, widget=None):
        old_img = self.img_chooser.get_filename()
        old_alt_text = get_textview_contents(self.alt_text)
        res = self.img_dialog.run()
        self.img_dialog.hide()
        if res == 1: # Attach
            self.attached_media = self.img_chooser.get_filename()
            if self.attached_media:
                self.media_desc = get_textview_contents(self.alt_text)
                self.img_button.set_label("Edit attached image")
        elif res == -1: # Remove
            self.img_chooser.unselect_all()
            self.reset_img_preview()
            self.alt_text.get_buffer().set_text("")
            self.attached_media = None
            self.media_desc = None
            self.img_button.set_label("Add image")
        elif res == 0: # Cancel. Reset the dialog
            self.alt_text.get_buffer().set_text(old_alt_text)
            if old_img:
                self.img_chooser.set_filename(old_img)
                self.update_img_preview()
            else:
                self.img_chooser.unselect_all()
                self.reset_img_preview()
    
    def update_img_preview(self, widget=None):
        img_fname = self.img_chooser.get_filename()
        try:
            pixbuf = GdkPixbuf.Pixbuf.new_from_file(img_fname)
        except:
            print("Failed to preview image!")
            self.reset_img_preview()
        else:
            scaled = pixbuf.scale_simple(640, 480, GdkPixbuf.InterpType.BILINEAR)
            self.img_preview.set_from_pixbuf(scaled)

    def reset_img_preview(self):
        self.img_preview.set_from_icon_name("insert-image", Gtk.IconSize.DIALOG)

    def display_error(self, e):
        dlg = Gtk.MessageDialog(self.window, Gtk.DialogFlags.DESTROY_WITH_PARENT | Gtk.DialogFlags.MODAL,
             Gtk.MessageType.ERROR, Gtk.ButtonsType.CLOSE, str(e))
        dlg.run()
        dlg.destroy()

    def submit_status(self, entry):
        text = entry.get_text()
        if not text: return

        entry.set_sensitive(False)
        self.submit_toot(text)
        Gtk.main_quit()

    def submit_toot(self, text):
        media_ids = None
        if self.attached_media:
            self.label.set_text("Uploading image...")
            media = self.mastodon.media_post(self.attached_media, description=self.media_desc)
            media_ids = [media["id"]]

        cw_text = self.cw_entry.get_text() if self.cw_toggle.get_active() else None

        self.mastodon.status_post(text,
            in_reply_to_id=self.mastodon_reply_id, # Can be None, & that's OK.
            media_ids=media_ids,
            spoiler_text=cw_text,
        )


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
