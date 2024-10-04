from datetime import datetime, timedelta, tzinfo, date
import calendar
import re
import math

from dateutil.parser import parse
from dateutil.tz import gettz
from pytz import timezone, UTC
from typing import Union

from mastodon_tools.user import MastodonUser


def get_swim_date(
    day: str,
    now: Union[datetime, str] = datetime.now(UTC),
    tz: Union[str, tzinfo] = None,
) -> date:
    """
    Returns the date of the last occurrence of a specific weekday before a given date,
    or the current date or the date of yesterday, depending on the value of the 'day' argument.

    Parameters:
    day (str): The day of the week as a string ("Monday", "Tuesday", etc.), "Today", or "Yesterday".
    now (Union[datetime, str], optional): The date from which to calculate the last occurrence of the weekday,
                                          either as a datetime object or as a string in the ISO 8601 format
                                          ("YYYY-MM-DD").
                                          Defaults to the current date and time.
    tz (Union[str, tzinfo], optional): The timezone to which the 'now' date should be converted.
                                                Can be a string or a tzinfo object.
                                                Defaults to 'UTC'.

    Returns:
    str: The date of the last occurrence of the weekday specified in the 'day' argument before the 'now' date,
         or the 'now' date if 'day' is "Today", or the date of yesterday if 'day' is "Yesterday", formatted as a string
         in the ISO 8601 format ("YYYY-MM-DD").7
    """
    # If 'now' is a string, convert it to a datetime object
    if isinstance(now, str):
        now = parse(now).replace(tzinfo=UTC)

    # If 'tz' is not specified, use the local timezone
    if tz is None:
        tz = gettz(None)

    # If 'tz' is a string, convert it to a datetime.tzinfo object
    if isinstance(tz, str):
        tz = timezone(tz)

    # Convert 'now' to the specified timezone
    now = now.astimezone(tz)

    if day == "Today":
        return now.date()
    elif day == "Yesterday":
        return (now - timedelta(days=1)).date()
    else:
        # Get the weekday as an integer
        weekday_int = list(calendar.day_name).index(day)
        # Get the difference between the current weekday and the target weekday
        diff = (now.weekday() - weekday_int) % 7
        # If the difference is 0, it means today is the target weekday, so we subtract 7 to get the last occurrence
        if diff == 0:
            diff = 7
        # Subtract the difference from the current date to get the date of the last occurrence of the target weekday
        return (now - timedelta(days=diff)).date()


regex = re.compile(
    r"<p>(?P<day>(To|Yester|Mon|Tues|Wednes|Thurs|Fri|Satur|Sun)day).*: (?P<lapcount>[\d\.]*) laps for (?P<distance>\d*)m"
)


class MastodonSwimmer(MastodonUser):
    def __init__(self, email: str):
        super().__init__(email)

    @property
    def swims(self):
        result = [
            {
                "date": get_swim_date(
                    status["regex"]["day"],
                    now=status["created_at"],
                ).strftime("%Y-%m-%d"),
                "laps": status["regex"]["lapcount"],
                "distance": status["regex"]["distance"],
                "uri": status["uri"],
            }
            for status in [
                {
                    "created_at": status["created_at"],
                    "regex": re.search(
                        regex,
                        status["content"],
                    ),
                    "content": status["content"],
                    "uri": status["uri"],
                }
                for status in [
                    {
                        "created_at": status["created_at"],
                        "content": status["content"],
                        "tags": [tag["name"] for tag in status["tags"]],
                        "uri": status["uri"],
                    }
                    for status in self.statuses.values()
                ]
                if "swim" in status["tags"]
                and status["created_at"].startswith(str(datetime.now().year))
            ]
        ]

        return sorted(
            result,
            key=lambda status: datetime.strptime(status["date"], "%Y-%m-%d"),
        )

    @property
    def total_swims(self):
        return len(self.swims)

    @property
    def total_laps(self):
        return sum(float(swim["laps"]) for swim in self.swims)

    @property
    def total_distance(self):
        return sum(int(swim["distance"]) for swim in self.swims)

    @property
    def remaining_distance(self):
        return 100000 - self.total_distance

    @property
    def remaining_days(self):
        today = datetime.now().date()
        last_day_of_year = datetime(today.year, 12, 31).date()
        remaining_days = (last_day_of_year - today).days
        if any(swim["date"] == today.strftime("%Y-%m-%d") for swim in self.swims):
            remaining_days -= 1
        return remaining_days

    @property
    def average_distance(self):
        return math.ceil(
            self.remaining_distance / self.remaining_days
            if self.remaining_days > 0
            else 0
        )

    @property
    def average_laps(self):
        return math.ceil(self.average_distance / 25)

    @property
    def statistics(self):
        return {
            "total_laps": self.total_laps,
            "total_distance": self.total_distance,
            "remaining_distance": self.remaining_distance,
            "remaining_days": self.remaining_days,
            "required_average_distance": self.average_distance,
            "required_average_laps": self.average_laps,
        }
