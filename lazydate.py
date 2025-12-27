'''
This is a lazy module wrapping python's `datetime` utility.
Dates are handled in Numeric type (float | int), expressed as days since the _ORIGIN, 2000-Jan-01.

That is,
0.0 means 2000-Jan-01 00:00:00
1.5 means 2000-Jan-02 12:00:00

The functions convert the values from Numeric to and from the other 3 conventions:
    Numeric: float or integers, as days since _ORIGIN

    datetime: datetime.datetime
    date: integers of year, month, day, ...
    string: string of YYYY-MM-DD, ...

----
lkkbox 20251227
'''
from datetime import datetime, timedelta
from math import isnan, isinf, floor
from typing import Literal, TypeAlias
from dateutil.parser import parse as parseDate
from calendar import isleap as cisleap

Numeric: TypeAlias = int | float


_ORIGIN_YEAR: int = 2000
_ORIGIN_MONTH: int = 1
_ORIGIN_DAY: int = 1
_ORIGIN: datetime = datetime(_ORIGIN_YEAR, _ORIGIN_MONTH, _ORIGIN_DAY)


# ---- from the other 3 conventions to num
def datetime2num(d: datetime) -> float:
    '''
    Compute the relative days since _ORIGIN from a datetime object.

    ------
    input
        d: datetime class

    ------
    output
        num: days relative to _ORIGIN

    ------
    example
        d = datetime(2000, 1, 5)
        num = _datetime2num(d)
    '''
    return (d - _ORIGIN).total_seconds() / 86400


def date2num(
    year: int,
    month: int,
    day: int,
    hour: int = 0,
    minute: int = 0,
    second: int = 0,
    microsecond: int = 0,
) -> float:
    '''
    Compute the relative days from _ORIGIN.

    ------
    input
        year: int
        month: int
        day: int
        hour: int=0
        minute: int=0
        second: int=0
        microsecond: int=0

    ------
    output
        num: days relative to _ORIGIN

    ------
    example
        num = date2num(2000, 1, 5)
    '''
    return datetime2num(datetime(year, month, day, hour, minute, second, microsecond))


def str2num(date_string: str, formatter: str | None = None) -> float:
    '''
    Compute the relative days from _ORIGIN.

    ------
    input
        date_string
        formatter: 
            None: auto formatter by `dateutil.parser`
            string: specified formatter  accepted by datetime.strptime

    ------
    output
        num: days relative to _ORIGIN

    ------
    example
        num = str2num('2000-1-5')
        num = str2num('01052000', '%m%d%Y')
    '''
    if formatter is None:
        return datetime2num(parseDate(date_string))

    else:
        return datetime2num(datetime.strptime(date_string, formatter))


# ---- from num to the other 3 conventions
def num2datetime(num: Numeric) -> datetime | float:
    '''
    Generate a datetime object from numeric as days relative to _ORIGIN

    ------
    input
        num: days relative to _ORIGIN

    ------
    output
        d: 
            datetime class         if num is finite
            math.inf or math.nan   otherwise

    ------
    example
        d = num2datetime(4.0)
        d = num2datetime(math.inf)
        d = num2datetime(math.nan)
    '''
    if isinf(num) | isnan(num):
        return num
    return _ORIGIN + timedelta(days=num)


def num2date(num: Numeric, n_returns: Literal[1, 2, 3, 4, 5, 6, 7] = 3) -> tuple[int]:
    '''
    Generate a tuple of integers (year, month, day, ....) from numeric as days relative to _ORIGIN.

    ------
    input
        num: days relative to _ORIGIN
        n_returns: number of fields to return, default=3

    ------
    output
        tuple[int * n_returns]: 
            1 -> return year
            2 -> return year, month
            3 -> return year, month, day
            ...

    ------
    example
        year, month, day = num2date(4.0)
        year, month, day, hour = num2date(5.25, 4)
    '''
    d = num2datetime(num)
    return (
        d.year,
        d.month,
        d.day,
        d.hour,
        d.minute,
        d.second,
        d.microsecond,
    )[:n_returns]


def num2str(num: float, formatter: str = '%Y%m%d') -> str:
    '''
    Formatting the date from a number.

    ------
    input
        num: days relative to _ORIGIN
        formatter: string accepted by datetime.strftime (default='%Y%m%d')

    ------
    output
        date_string

    ------
    example
        formatted = num2str(date2num(2003, 1, 8), '%Y-%m-%d')
    '''
    return num2datetime(num).strftime(formatter)


# ---- other date manipulations for num
def months_between(num1: Numeric, num2: Numeric) -> int:
    '''
    return the number of months between num1 and num2
    ----
    example
        n = months_between(
            date2num(2000, 1, 1),
            date2num(2000, 3, 1),
        ) # n = 2

        n = months_between(
            date2num(2000, 4, 1),
            date2num(1999, 12, 1),
        ) # n = -4
    '''
    year1, month1 = num2date(num1, n_returns=2)
    year2, month2 = num2date(num2, n_returns=2)
    return 12 * (year2 - year1) + (month2 - month1)


def add_month(num: Numeric, delta: int = 1, warning: bool = True) -> Numeric:
    year, month, day = num2date(num, n_returns=3)
    remains = num % 1

    max_n_years = abs(delta) // 12 + 1

    month += delta

    for _ in range(max_n_years):  # finite loop just to be safe
        if 1 <= month and month <= 12:
            break

        if month > 12:  # advance a year
            year += 1
            month -= 12

        if month < 1:  # backoff a year
            year -= 1
            month += 12

    num1stOfMonth = date2num(year, month, 1)
    dim = ndays_in_month(num1stOfMonth)
    if day > dim:
        if warning:
            print(
                f'Warning (addmonth): day is changed from {day} to {dim} for {year}-{month}-{day}'
            )

        day = dim

    return num1stOfMonth + (day - 1) + remains


# ---- utilities
def now():
    '''
    return the numbers of days from _ORIGIN to now

    ----
    SYNTAX
        num = now()
        print(num2str(num, '%Y-%m-%d %H:%M:%S'))
    '''
    return datetime2num(datetime.now())


def today():
    '''
    return the numbers of days from _ORIGIN to today
    equivalent to `floor(now())`

    ----
    SYNTAX
        num = now()
        print(num2str(num, '%Y-%m-%d %H:%M:%S'))
    '''
    return floor(now())


def is_leap(num: Numeric) -> bool:
    '''True if the year of the input date number is a leap year'''
    return cisleap(year(num))


def is_leap_year(year: int) -> bool:
    '''True if the input year is a leap year'''
    return cisleap(year)


def ndays_in_month(num: Numeric) -> Literal[28, 29, 30, 31]:
    '''
    compute the number of days in the month

    ----
    SYNTAX
        dim = ndays_in_month(date2num(2000, 2, 3))
        print(dim)

    '''
    year, month = num2date(num, n_returns=2)
    d = num2datetime(num)
    d.timetuple().tm_wday

    if month in [1, 3, 5, 7, 8, 10, 12]:
        return 31

    elif month in [4, 6, 9, 11]:
        return 30

    elif month == 2:
        if not cisleap(year):
            return 28

        else:
            return 29


def day_of_year(num: Numeric) -> int:
    return num2datetime(num).timetuple().tm_yday


def day_of_week(num):
    return num2datetime(num).timetuple().tm_wday


# ---- lazier shortcut
def year(num: Numeric) -> int:
    '''return the year of the input date number'''
    return num2datetime(num).year


def month(num: Numeric) -> int:
    '''return the month of the input date number'''
    return num2datetime(num).month


def day(num: Numeric) -> int:
    '''return the day of the input date number'''
    return num2datetime(num).day


def hour(num: Numeric) -> int:
    '''return the hour of the input date number'''
    return num2datetime(num).hour


def minute(num: Numeric) -> int:
    '''return the minute of the input date number'''
    return num2datetime(num).minute


def day(num: Numeric) -> int:
    '''return the day of the input date number'''
    return num2datetime(num).day


def microsecond(num: Numeric) -> int:
    '''return the microsecond of the input date number'''
    return num2datetime(num).microsecond


# ---- to be deprecated
def dayOfYear229(f):
    doy = dayOfYear(f)
    if doy <= 31 + 28:  # Feb-28
        return doy
    if isleap(f):
        return doy
    return doy + 1  # skipped 229


def dayOfClim(f, keepDecimals=False):
    __, m, d, remains = *float2ymd(f), f % 1
    out = ymd2float(2000, m, d) - ymd2float(2000, 1, 1)
    if keepDecimals:
        out += remains
    return out


def times2string(times, formatter='%Y%m%d', joiner='-', indices=[0, -1]):
    strings = [float2format(times[i], formatter) for i in indices]
    strings = [s for i, s in enumerate(strings) if s not in strings[:i]]
    return joiner.join(strings)
