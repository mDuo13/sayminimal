# SayMinimal

SayMinimal is a simple, write-only¹ Twitter client. The point of SayMinimal is to map it to a keypress so you can press a button, comment on something, and then go back to what you were doing before.

¹Technically SayMinimal also read your most recent tweet when you ask it to thread tweets together.

## Setup

SayMinimal requires Python 3, Gtk+ 3, and [PyGObject](https://pygobject.readthedocs.io/en/latest/).

After that, the GUI should walk you through OAuth setup. Basically, you can choose to use the default Consumer Key pair that's hard-coded into the app, or you can provide your own. I recommend you provide your own because random people can find and abuse consumer keys that are published along with the source. You also need to authorize the app to read and write to your Twitter account (verifying it with a PIN).

## Config

SayMinimal saves its configuration in `~/.config/sayminimal/conf.yml`, which you can delete at any time to reset. The only conf saved in the current version is the four OAuth keys.

## Keyboard Shortcuts

- **Enter** - Send the current tweet.
- **Shift-Enter** - Add a newline to your tweet. (It displays funky in the input text box but works)
- **Alt+I** - Browse for an image to attach to the current tweet. SayMinimal only supports 1 image per tweet (not the 4 Twitter properly supports).
- **Alt+T** - Thread this tweet as a reply to your most recent previous tweet. Press again to toggle off.
