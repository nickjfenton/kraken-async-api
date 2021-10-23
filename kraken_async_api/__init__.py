"""
This package provides an API for accessing the Kraken Exchange via Websockets
and REST.

The :class:`Kraken` class is recommended and provides a high level API that
abstracts away details of the communications protocol and token refreshing.

For lower level access and control, the *Api classes can be used to access
endpoints, grouped by communications protocol (REST or Websockets) and authorisation
(Public or Private).
"""
from .exchange import Kraken
from .config import Config
from .rest import PublicRestApi, PrivateRestApi
from .websocket import PublicWebSocketApi, PrivateWebSocketApi
from .constants import Depth, Interval, AssetClass
