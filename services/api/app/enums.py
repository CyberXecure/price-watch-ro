from enum import Enum


class MeasureType(str, Enum):
    VOLUME = "volume"
    WEIGHT = "weight"
    COUNT = "count"
    UNKNOWN = "unknown"


class ComparisonUnit(str, Enum):
    LEI_PER_L = "lei/l"
    LEI_PER_KG = "lei/kg"
    LEI_PER_BUC = "lei/buc"
    TOTAL = "total"


class PriceStatus(str, Enum):
    HIGH_PRICE = "high_price"
    NORMAL = "normal"
    BEST_BUY = "best_buy"
