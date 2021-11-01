"""Constants used by the Kraken Exchange API"""
from dataclasses import dataclass
from enum import Enum


class Interval(Enum):
    """
    OHLC interval parameter options when calling :py:meth:`PublicRestApi.get_ohlc_data`

    Intervals are given in minutes.
    """
    I1 = 1
    I5 = 5
    I15 = 15
    I30 = 30
    I60 = 60
    I240 = 240
    I1440 = 1440
    I10080 = 10080
    I21600 = 21600


class Depth(Enum):
    """
    Depth associated with book subscription in number of levels each side
    """
    D10 = 10
    D25 = 25
    D100 = 100
    D500 = 500
    D1000 = 1000


@dataclass
class Header:
    """
    Headers sent on REST calls
    """
    API_KEY = "API-KEY"
    API_SIGN = "API-Sign"


class AssetClass(Enum):
    """Asset classes"""
    CURRENCY = "currency"


class InfoType(Enum):
    """
    Options for the 'info' parameter when calling
    :meth:`PublicRestApi.get_asset_pairs`
    """
    INFO = "info"
    LEVERAGE = "leverage"
    FEES = "fees"
    MARGIN = "margin"
