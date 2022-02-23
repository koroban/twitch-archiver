import logging
import m3u8

from datetime import datetime
from random import randrange

from src.api import Api


class Twitch:
    """
    Functions and processes for interacting with the Twitch API.
    """
    def __init__(self, client_id=None, client_secret=None, oauth_token=None):
        """Class constructor.

        :param client_id: twitch client_id
        :param client_secret: twitch client_secret
        :param oauth_token: twitch oauth_token
        """
        self.log = logging.getLogger()

        self.client_id = client_id
        self.client_secret = client_secret
        self.oauth_token = oauth_token

    def get_api(self, api_path):
        """Retrieves information from the Twitch API.

        :param api_path: twitch api endpoint to send request to
        :return: requests response json
        """
        _h = {'Authorization': 'Bearer ' + self.oauth_token, 'Client-Id': self.client_id}
        _r = Api.get_request('https://api.twitch.tv/helix/' + api_path, h=_h)

        return _r.json()

    def generate_oauth_token(self):
        """Generates an OAuth token from the provided client ID and secret.

        :return: oauth token
        """
        _d = {'client_id': self.client_id, 'client_secret': self.client_secret,
              'grant_type': 'client_credentials'}
        _t = Api.post_request('https://id.twitch.tv/oauth2/token', d=_d).json()['access_token']

        return _t

    def validate_oauth_token(self):
        """Validates a specified OAuth token with Twitch.

        :return: token expiration date
        """
        self.log.debug('Verifying OAuth token.')
        _h = {'Authorization': 'Bearer ' + self.oauth_token}
        _r = Api.get_request('https://id.twitch.tv/oauth2/validate', h=_h)
        self.log.info('OAuth token verified successfully. Expiring in ' + str(_r.json()['expires_in']))

        return _r.json()['expires_in']

    @staticmethod
    def get_playback_access_token(vod_id):
        """Gets a playback access token for a specified vod.

        :param vod_id: id of vod to retrieve token for
        :return: playback access token
        """
        # only accepts the default client ID for non-authenticated clients
        _h = {'Client-Id': 'kimne78kx3ncx6brgo4mv6wki5h1ko'}
        _q = """
        {{
            videoPlaybackAccessToken(
                id: {vod_id},
                params: {{
                    platform: "web",
                    playerBackend: "mediaplayer",
                    playerType: "site"
                }}
            ) {{
                signature
                value
            }}
        }}
        """.format(vod_id=vod_id)
        _r = Api.post_request('https://gql.twitch.tv/gql', j={'query': _q}, h=_h)

        return _r.json()['data']['videoPlaybackAccessToken']

    def get_vod_index(self, vod_id):
        """Retrieves an index of m3u8 streams.

        :param vod_id: id of vod to retrieve index of
        :return: url of m3u8 playlist
        """
        access_token = self.get_playback_access_token(vod_id)

        _p = {
            'player': 'twitchweb',
            'nauth': access_token['value'],
            'nauthsig': access_token['signature'],
            'allow_source': 'true',
            'playlist_include_framerate': 'true',
            'p': randrange(1000000, 9999999)
        }
        _r = Api.get_request(f'https://usher.ttvnw.net/vod/{vod_id}.m3u8', p=_p)

        _index = m3u8.loads(_r.text)
        # extract source (chunked) playlist uri from m3u8 data
        for _p in _index.playlists:
            if _p.media[0].group_id == 'chunked':
                return _p.uri

    @staticmethod
    def get_channel_hls_index(channel):
        """Retrieves an index of a live m3u8 stream.

        :param channel: name of channel to retrieve index of
        :return: url of m3u8 playlist
        """
        channel = channel.lower()

        access_token = Twitch.get_stream_playback_access_token(channel)

        _p = {
            'player': 'twitchweb',
            'fast_bread': 'true',
            'token': access_token['value'],
            'sig': access_token['signature'],
            'allow_source': 'true',
            'playlist_include_framerate': 'true',
            'player_backend': 'mediaplayer',
            'supported_codecs': 'avc1',
            'p': randrange(1000000, 9999999)
        }
        _r = Api.get_request(f'https://usher.ttvnw.net/api/channel/hls/{channel}.m3u8', p=_p)

        _index = m3u8.loads(_r.text)

        # extract source (chunked) playlist uri from m3u8 data
        for _p in _index.playlists:
            if _p.media[0].group_id == 'chunked':
                return _p.uri

    @staticmethod
    def get_stream_playback_access_token(channel):
        """Gets a stream access token for a specified channel.

        :param channel: channel name to retrieve token for
        :return: playback access token
        """
        # only accepts the default client ID for non-authenticated clients
        _h = {'Client-Id': 'kimne78kx3ncx6brgo4mv6wki5h1ko'}
        _q = """
        {{
            streamPlaybackAccessToken(
                channelName: "{channel}",
                params: {{
                    platform: "web",
                    playerBackend: "mediaplayer",
                    playerType: "embed"
                }}
            ) {{
                signature
                value
            }}
        }}
        """.format(channel=channel.lower())
        _r = Api.post_request('https://gql.twitch.tv/gql', j={'query': _q}, h=_h)

        return _r.json()['data']['streamPlaybackAccessToken']

    def get_vod_status(self, vod_json):
        try:
            # if stream live and vod start time matches
            stream_created_time = \
                datetime.strptime(self.get_api('streams?user_id=' + str(vod_json['user_id']))['data'][0]['started_at'],
                                  '%Y-%m-%dT%H:%M:%SZ').timestamp()
            vod_created_time = datetime.strptime(vod_json['created_at'], '%Y-%m-%dT%H:%M:%SZ').timestamp()
            # if vod created within 10s of stream created time
            if vod_created_time - stream_created_time <= 10 and stream_created_time - vod_created_time >= -10:
                self.log.debug('VOD creation time is within 10s of stream created time, running in live mode.')
                return True

        except IndexError:
            pass

        return False
