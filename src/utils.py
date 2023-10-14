from datetime import datetime, timedelta
from typing import Union


def set_date_args(parser):
    now = datetime.now()
    parser.add_argument('-d', '--day', type=int, default=now.day)
    parser.add_argument('-m', '--month', type=int, default=now.month)
    parser.add_argument('-y', '--year', type=int, default=now.year)


TimeArithmeticTypes = Union['Time', timedelta, int]


class Time:

    def __init__(self, spent_seconds: Union[int, timedelta]) -> None:
        if isinstance(spent_seconds, timedelta):
            spent_seconds = int(spent_seconds.total_seconds())
        self.spent_seconds = spent_seconds

    @property
    def human_readable(self) -> str:
        return f'{self.spent_seconds // 3600}h {self.spent_seconds % 3600 // 60}m {self.spent_seconds % 60}s'

    @classmethod
    def __map_arithmetic__(cls, other: TimeArithmeticTypes) -> int:
        if isinstance(other, int):
            return other
        elif isinstance(other, timedelta):
            return int(other.total_seconds())
        elif isinstance(other, Time):
            return other.spent_seconds
        return NotImplemented

    def __add__(self, other: TimeArithmeticTypes) -> 'Time':
        return Time(self.spent_seconds + self.__map_arithmetic__(other))

    def __radd__(self, other: TimeArithmeticTypes) -> 'Time':
        return Time(self.__map_arithmetic__(other) + self.spent_seconds)

    def __sub__(self, other: TimeArithmeticTypes) -> 'Time':
        return Time(self.spent_seconds - self.__map_arithmetic__(other))

    def __rsub__(self, other: TimeArithmeticTypes) -> 'Time':
        return Time(self.__map_arithmetic__(other) - self.spent_seconds)

    def __repr__(self) -> str:
        return f'Time("{self.human_readable}")'
