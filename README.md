# Matrix Social Media Poster Base Poster
Author: polyma3000

## How to set up

### Setup connections

To access the Platform connections, we need to create a config file.

Let's create `connections.yaml`:

```yaml
mastodon_connections:
  connection_name:
    domain: "https://your.domain"
    token: "your_token"
```

To get the credentials just go to your settings and under the `developer` menu there is a place to create a new app and get your credentials all in one go.

Visit https://tinysubversions.com/notes/mastodon-bot/ if the version of your server has an old version which doesn't allow you to get credentials.

For other platforms use the name of the platform and add `_connections` in the top hierarchy of your `connections.yaml`

### Derive Message Class
At first, you have to create an own Message class derived from basis_poster.Message and overload the async method send_to_platform.
This example is based on `mastodon.py`.

Let's create `MyMessage.py`:
```python
from basis_poster import Message
from mastodon import Mastodon
from mastodon.Mastodon import MastodonNetworkError
from urllib3.exceptions import ConnectTimeoutError, MaxRetryError

class MyMessage(Message):
    async def send_to_platform(self, platform_connection: Mastodon):
        pictures = []
        if self.pictures_names:
            for picture_name in self.pictures_names:
                pictures.append(
                    platform_connection.media_post(media_file=picture_name))

        if pictures:
            posted_posts = [platform_connection.status_post(
                status=self.posts.pop(0), media_ids=pictures)]
        else:
            posted_posts = [platform_connection.status_post(
                status=self.posts.pop(0))]

        while self.posts:
            posted_posts.append(platform_connection.status_post(status=self.posts.pop(0),
                                                                in_reply_to_id=posted_posts[len(posted_posts) - 1]))
    
    @classmethod
    def get_errors(cls):
        return TimeoutError, ConnectTimeoutError, MaxRetryError, MastodonNetworkError
```

In `self.pictures_names` the filenames of the pictures are listed.
In `self.posts` the posts to send are available.

### Derive PlatformHandler Class
At first, you have to create an own `PlatformHandler` class derived from `basis_poster.PlatformHandler` and overload the static method `add_platform_connection`.
This example is based on `mastodon.py`.

Let's create `MyPlatformHandler.py`:
```python
from basis_poster import PlatformHandler
from mastodon import Mastodon

class MyPlatformHandler(PlatformHandler):
    @staticmethod
    def add_platform_connection(platform_connection_name: str, platform_connection: dict):
        return Mastodon(
                access_token=platform_connection['token'],
                api_base_url=platform_connection['domain'],
            )
```

`platform_connection` hands over the data stored for this connection in `connections.yaml`.


### Use Platform Handler
To start your Platform we need to set up the PlatformHandler and start it.

Let's create `main.py`:

```python
from MyMessage import MyMessage
from MyPlatformHandler import MyPlatformHandler

import logging

def main():
    logging.getLogger().debug('Started..')
    
    handler = MyPlatformHandler(
        MyMessage,
        'mastodon',
        500,
        db_filename="shared_messages.db",
        connections_filename="connections.yaml",
        pictures_directory_name="pictures"
    )
    
    handler.run()
    
    logging.getLogger().debug('Finished..')

if __name__ == '__main__':
    main()
```

`db_filename` ist the path to the sqlite database, where the `PlatformHandler` gets the messages to send from.
`connections_filename` ist the path to the connections config we set up above.
`pictures_directory_name` ist the path to the pictures to send with messages.

### How to set up the database

## Possible simple connections
- https://github.com/halcy/Mastodon.py
- https://github.com/python-telegram-bot/python-telegram-bot
