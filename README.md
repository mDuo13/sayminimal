# SayMinimal

SayMinimal is a simple, write-only¹ client to [Mastodon](https://joinmastodon.org/). The point of SayMinimal is to map it to a keypress so you can press a button, comment on something, and then go back to what you were doing before.

¹Technically SayMinimal also reads your most recent status when you ask it to thread toots together.

## Setup

SayMinimal requires Python 3, Gtk+ 3, and [PyGObject](https://pygobject.readthedocs.io/en/latest/).

If you've got those taken care of, you can install SayMinimal with `pip`:

    sudo pip3 install sayminimal

After that, the GUI should walk you through OAuth setup. Basically, you can choose to use the default Consumer Key pair that's hard-coded into the app, or you can provide your own. I recommend you provide your own because random people can find and abuse consumer keys that are published along with the source.

## Config

SayMinimal saves its configuration in `~/.config/sayminimal/conf.yml`, which you can delete at any time to reset. The only conf saved in the current version is the four OAuth keys.

## Keyboard Shortcuts

- **Enter** - Send the current status.
- **Esc** - Exit without sending.
- **Shift-Enter** - Add a newline to your status. (It displays funky in the input text box but works)
- **Alt-I** - Browse for an image to attach to the current status. SayMinimal currently only supports 1 media file per toot.
- **Alt-T** - Thread this status as a reply to your most recent previous status. Press again to toggle off.
- **Alt-C** - Toggle content warning on post.


## What happened to Twitter?

SayMinimal originated as a Twitter client before adding Mastodon support. For various reasons, most notably Twitter intentionally breaking the API, SayMinimal v4.0 no longer works with Twitter. Any future development (no promises) will be focused on better Mastodon support.
