﻿```
 _______ ___ ___ ___ _______ _______ ___ ___  _______ _______ _______ ___ ___ ___ ___ ___ _______ _______ 
|       |   Y   |   |       |   _   |   Y   ||   _   |   _   |   _   |   Y   |   |   Y   |   _   |   _   \
|.|   | |.  |   |.  |.|   | |.  1___|.  1   ||.  1   |.  l   |.  1___|.  1   |.  |.  |   |.  1___|.  l   /
`-|.  |-|. / \  |.  `-|.  |-|.  |___|.  _   ||.  _   |.  _   |.  |___|.  _   |.  |.  |   |.  __)_|.  _   1
  |:  | |:      |:  | |:  | |:  1   |:  |   ||:  |   |:  |   |:  1   |:  |   |:  |:  1   |:  1   |:  |   |
  |::.| |::.|:. |::.| |::.| |::.. . |::.|:. ||::.|:. |::.|:. |::.. . |::.|:. |::.|\:.. ./|::.. . |::.|:. |
  `---' `--- ---`---' `---' `-------`--- ---'`--- ---`--- ---`-------`--- ---`---' `---' `-------`--- ---'
```
<p align="center"><b>
A simple, fast, platform-independent Python script for downloading past and present Twitch VODs and chat logs.</b><br/>
<br>
Primarily focused on data preservation, this script can be used to archive an entire Twitch channel at once, or to quickly grab the chat log from a single VOD. Both archived, and live VODs can be downloaded with this script.
</p>



## NOTICE: Chat archiving is currently not working as Twitch has changed the API - this should be fixed in the next few days but for now add the'-v' flag to only grab the video until an update is released.



## Table of Contents

  * [Features](#features)
  * [Requirements](#requirements)
  * [Installation & Usage](#installation--usage)
    * [Installation](#installation)
    * [Usage](#usage)
    * [Arguments](#arguments)
    * [Configuration](#configuration)
  * [Retrieving Tokens](#retrieving-tokens)
  * [Extra Info](#extra-info)
    * [Running as a Service](#running-as-a-service)
    * [Notes](#notes)
    * [How files are stored](#how-files-are-stored)
    * [Planned Features](#planned-features)
    * [Why?](#why)
  * [Disclaimer](#disclaimer)

## Features
* Allows any number of VODs or channels to be downloaded simultaneously.
* VODs can be downloaded as fast as your Internet connection (and storage) can handle.[^1]
* Allows the downloading of **live** VODs *before sections can be muted or deleted*.[^2]
* Generates and saves a readable chat log with timestamps and user badges.
* Allows for the archiving of both video and chat logs.
* Supports archiving streams without an associated VOD.
* Error notifications sent via pushbullet.
* Requires minimal setup or external programs.

[^1]: If you wish to speed up (or slow down) the downloading of VOD pieces, supply the '--threads NUMBER' argument to the script. This changes how many download threads are used to grab the individual video files. With the default of 20, I can max out my gigabit Internet while downloading to an M.2 drive.
[^2]: There is one caveat with live archiving due to how Twitch presents ads. Ads are not downloaded, BUT while an ad is displayed, the actual stream output is not sent. This can result in missing segments under very rare circumstances, but any missing segments should be filled via a parallel VOD archival function. 

## Requirements
* **[Python](https://www.python.org/) >= 3.7**
* Python **requests** and **m3u8** modules `python -m pip install requests m3u8` or `python -m pip install -r requirements.txt`
* **[FFmpeg](https://ffmpeg.org/) >= 4.3.1** and **ffprobe** (Accessible via your PATH - see [Installation](#installation))

## Installation & Usage
### Installation
1. Download the most recent release via the green "Code" button on the top right, or grab the latest stable [release](https://github.com/Brisppy/twitch-archiver/releases/latest).

2. Download [FFmpeg](https://ffmpeg.org/download.html) and add to your PATH. See [this](https://www.wikihow.com/Install-FFmpeg-on-Windows) article if you are unsure how to do this.

3. Unpack and open the twitch-archiver folder and install required Python modules `python -m pip install -r requirements.txt`.

4. Run twitch-archiver once with `python ./twitch-vod-archiver.py -i CLIENT_ID -s CLIENT_SECRET -v 0`, supplying your client-id with `-i CLIENT_ID` and client-secret with `-s CLIENT_SECRET` to save your credentials to the configuration. You will only ever need to do this once. You can then view the saved configuration with `python ./twitch-archiver.py --show-config`.

5. You should now be ready to save channels and VODs with the script, use `python ./twitch-vod-archiver.py -h` to see available arguments and how to use them.

### Usage
Run the script via your terminal of choice. Use ```python ./twitch-vod-archiver.py -h``` to view help text.

#### Examples
```# python ./twitch-archiver.py -c Brisppy -i {client_id} -s {client_secret} -d "Z:\\twitch-archive"```

Would download `video` and `chat` of all VODs from the channel `Brisppy`, using the provided `client_id` and `client_secret`, to the directory `Z:\twitch-archive`.

```# python ./twitch-archiver.py -v 1276315849,1275305106 -d "/mnt/twitch-archive" -V -t 10```

Would download VODs `1276315849` and `1275305106` to the directory `/mnt/twitch-archive`, only saving the `video`  using `10 download threads`.

#### Arguments
Below is the output of the `--help` or `-h` command. This displays all the available arguments and a brief description of how to use them.
```
usage: twitch-archiver.py [-h] (-c CHANNEL | -v VOD_ID) [-i CLIENT_ID] [-s CLIENT_SECRET] [-C] [-V]
                          [-t THREADS] [-q QUALITY] [-d DIRECTORY] [-w] [-L LOG_FILE] [-I CONFIG_DIR]
                          [-p PUSHBULLET_KEY] [-Q | -D] [--version] [--show-config]

requires one of:
    -c CHANNEL, --channel CHANNEL
            Channel(s) to download, comma separated if multiple provided.
    -v VOD_ID, --vod-id VOD_ID
            VOD ID(s) to download, comma separated if multiple provided.

credentials are grabbed from stored config, OR provided with:
    -i CLIENT_ID, --client-id CLIENT_ID
            Client ID retrieved from dev.twitch.tv
    -s CLIENT_SECRET, --client-secret CLIENT_SECRET
            Client secret retrieved from dev.twitch.tv

Both the video and chat logs are grabbed if neither are specified.

optional arguments:
  -h, --help            show this help message and exit
  -c CHANNEL, --channel CHANNEL
                        A single twitch channel to download, or multiple comma-separated channels.
  -v VOD_ID, --vod-id VOD_ID
                        A single VOD (e.g 12763849) or many comma-separated IDs (e.g 12763159,12753056).
  -i CLIENT_ID, --client-id CLIENT_ID
                        Client ID retrieved from dev.twitch.tv
  -s CLIENT_SECRET, --client-secret CLIENT_SECRET
                        Client secret retrieved from dev.twitch.tv
  -C, --chat            Only save chat logs.
  -V, --video           Only save video.
  -t THREADS, --threads THREADS
                        Number of video download threads. (default: 20)
  -q QUALITY, --quality QUALITY
                        Quality to download. Options are 'best', 'worst' or a custom value.
                        Format for custom values is [resolution]p[framerate], (e.g 1080p60, 720p30).
                        (default: best)
  -d DIRECTORY, --directory DIRECTORY
                        Directory to store archived VOD(s), use TWO slashes for Windows paths.
                        (default: $CURRENT_DIRECTORY)
  -w, --watch           Continually check every 10 seconds for new streams from the specified channel.
  -S, --stream-only     Only download streams which are currently live.
  -N, --no-stream       Don't download streams which are currently live.
  -L LOG_FILE, --log-file LOG_FILE
                        Output logs to specified file.
  -I CONFIG_DIR, --config-dir CONFIG_DIR
                        Directory to store configuration, VOD database and lock files.
                        (default: $HOME/.config/twitch-archiver)
  -p PUSHBULLET_KEY, --pushbullet-key PUSHBULLET_KEY
                        Pushbullet key for sending pushes on error. Enabled by supplying key.
  -Q, --quiet           Disable all log output.
  -D, --debug           Enable debug logs.
  --version             Show version number and exit.
  --show-config         Show saved config and exit.
```

#### Watch Mode
Watch mode can be used by adding the `-w` argument, repeatedly checking every 10 seconds for new VODs.

My recommendation is to set up a systemd service to manage the starting / restarting of twitch-archiver, see [Systemd Service Setup](#systemd-service-setup) for how this can be done.

#### Configuration
By default, configuration files are stored in `$HOME/.config/twitch-archiver`

This holds the config file (config.ini), VOD database used when archiving channels (vods.db), and is where lock files are stored to prevent multiple instances of TA from overwriting each other.

        CONFIG_DIR ─┬─ config.ini
                    │
                    ├─ vods.db
                    │
                    └─ .lock.xxxxxxx

#### Authentication Token Storage

Authentication tokens are stored in this file, the contents will be empty unless you supply the script with the relevant arguments (client id or secret) which will then be saved to this file. Here's what an empty file will look like:
```
[settings]
client_id = 
client_secret = 
oauth_token = 
pushbullet_key = 
```

You can view the stored configuration by supplying `--show-config` when you run the script, or edit the file manually - the default location being `$HOME/.config/twitch-archiver/config.ini`, where `$HOME` is your user directory.

These authentication parameters are loaded into TA **first**, but will be overwritten if you pass different authentication parameters to the script when running it.

*Note: the configuration file will be created the first time you use TA and an OAuth token is successfully generated. This requires a valid client ID and secret be provided*

## Retrieving Tokens
### To retrieve the CLIENT_ID and CLIENT_SECRET:
1. Navigate to [dev.twitch.tv](https://dev.twitch.tv/) and log in.
2. Register a new app called Twitch VOD Archiver with any redirect URL and under any Category.
3. The provided Client ID is used as the `CLIENT_ID` variable.
4. The provided Client Secret is used as the `CLIENT_SECRET` variable.

## Extra Info
### Running TA as a service
I would recommend running twitch-archiver as a service under Linux. This makes use of the watch mode to repeatedly look for new VODs or streams to download.

The below section covers the setup of the service, which can be reused for every channel you wish to archiver by simply repeating steps 3 through 5.

#### Systemd Service Setup
To run twitch-archiver as an automatic, self-restarting service:

First grab the service unit file and reload systemd.

    # wget https://gist.githubusercontent.com/Brisppy/cdaa7bd812b11c07fdbb16e935777a48/raw/f71a8db4da7fe7abfb0c3ef974834f15befc8930/twitch-archiver@.service -P /etc/system/systemd/
    # systemctl daemon-reload

Then start twitch-archiver replacing `CHANNEL` with the name of a channel you wish to archive. Repeat this for every channel you want to archive.

    # systemctl start twitch-archiver@CHANNEL.service
    # systemctl enable twitch-archiver@CHANNEL.service

### Notes
* Some streamers opt to place their music on a separate audio track which isn't archived by Twitch. Due to the way LIVE archiving is done with TA, the music may cut in and out intermittently, often due to an ad being played and the stream archiver not being able to grab those parts. To avoid this entirely, use the `--vod-only` option which will not have this track at all, though this archive is ~5 minutes delayed and so will miss the end of a VOD if it is deleted.
* We use the downloaded VOD duration to ensure that the VOD was successfully downloaded and combined properly, this is checked against Twitch's own API, which can show incorrect values. If you come across a VOD with a displayed length in the Twitch player longer than it actually goes for (If the VOD finishes before the timestamp end is reached), create a file named `.ignorelength` inside the VOD's directory (where `vod.json` and `verbose_chat.log` are stored), you may also want to verify that the VOD file matches the Twitch video after archiving too.
* If a VOD is deleted while it is being archived, all the vod information will be saved, and the VOD will be combined as-is and chat exported. 
* If your config (and thus vod database) is stored on an SMB/CIFS share, you may encounter issues with querying and adding to the sqlite database. This can be resolved by mounting the share with the `nobrl` option on linux.
* If you intend to push chat logs to an ELK stack, [this gist](https://gist.github.com/Brisppy/ddcf4d5bbb73f957181743faadb959e3) should have everything you need.
* By default, the highest quality VOD is downloaded. This can be changed via the `-q QUALITY` argument, where quality can be `best`, `worst`, or a custom value in the format `[resolution]p[framerate]`, for example `1080p60` or `720p30` would be valid values. If an exact match for the quality cannot be found, any quality of a matching **resolution** will be downloaded; for example, if you select `720p60`, and only `720p30` is available, `720p30` would be downloaded. Similarly, if you select `1080p30` and only `1080p60` is found, then `1080p60` would be downloaded instead. If no match is found, the highest quality will be downloaded.
* Debug logging only works on Linux. If you know how to get Python logging to work on all operating systems *with multiprocessing*, i'd be grateful if you could submit a PR with the required changes. 
* Dashboard uploads are not currently supported by the channel archiver. Only archived streams will be grabbed.

### How files are stored
VODs are downloaded to the specified directory. If downloading a channel, an individual folder will be created for that specific channel.
When supplying just VOD ID(s), the vod is downloaded to a folder inside the supplied directory.

        DIRECTORY ─┬─ CHANNEL_a ─┬─ VOD_a ─┬─ vod.mp4
                   │             │         │
                   │             │         ├─ vod.json
                   │             │         │
                   │             │         ├─ verbose_chat.json
                   │             │         │
                   │             │         └─ readable_chat.log
                   │             │
                   │             └─ VOD_b ─── *
                   │
                   ├─ CHANNEL_b ─┬─ VOD_c ─── *
                   │             │
                   │             └─ VOD_d ─── *
                   │
                   ├─ VOD_e ─┬─ vod.mp4
                   │         │
                   │         ├─ vod.json
                   │         │
                   │         ├─ verbose_chat.json
                   │         │
                   │         └─ readable_chat.log
                   │
                   └─ VOD_f ─── *

### Planned Features
- [x] .ts to .mp4 conversion progress bar.
- [x] Find a way to directly archive the stream - could be then spliced with downloaded vod parts to capture everything up to the point the VOD is deleted rather than just up to a couple of minutes before. Both video and chat could be done this way.
- [x] Speed up VOD part discovery by finding and removing downloaded parts from the 'to-download' list.
- [ ] Allow archiving of subscriber-only VODs (need an account with a subscription for development + testing).
- [ ] Improve VOD download speed using separate download and file move workers (may need someone to test with >1Gbit connection).
- [ ] Release python package.
- [x] Implement video archiving for streams without VODs.
- [ ] Implement chat archiving for streams without VODs.
- [ ] Track and store games played during streams.
- [ ] Create and release packaged .exe

### Why?
To put it simply - **I don't like when data is deleted**.

I originally began work on the first version of this script in response to the copyright storm in which most Twitch streamers purged their old VODs in fear of DMCA.

At the time, and even now I could not find any script which would allow for the AUTOMATED archival of both the video AND chat for a particular VOD, and especially not one which can do this while the VOD is still live.

This script seeks to cover this, while also offers other functionality for those with a penchant for archiving data, or who wish to download VODs for other reasons.

## Disclaimer
This script is intended to be used with the express permission of any involved rights holders, and is not intended to be used to duplicate, download or steal copyrighted content or information. When downloading VODs ensure you have permission from ALL involved rights holders for the content which you are downloading, and if you have the intention to share such content, you should also have explicit permission to do so.

If your intent is to use this script to lazily rip and upload streams to another platform for your own gain without the permission of the streamer, I implore you to stop and think about what you are doing and the possible effect of doing so, and politely request that you find another method with which to steal the work of others.
