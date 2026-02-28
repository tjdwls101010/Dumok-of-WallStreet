#!/usr/bin/env python3
"""FOMC meeting calendar with official Federal Reserve meeting schedule.

Provides static calendar of Federal Open Market Committee (FOMC) meetings for 2026.
All times are in UTC. Source: Federal Reserve official meeting calendar at
https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm

Args:
	current_time (datetime): Optional current time for next meeting calculation (defaults to now)

Returns:
	Functional API:
	- get_next_meeting_time(current_time=None): Returns datetime of next upcoming FOMC meeting
	- get_all_meetings(): Returns list of all scheduled FOMC meetings with metadata

	get_all_meetings() returns:
	list: [
		{
			"datetime": datetime,				# Meeting datetime object (UTC)
			"date_str": str,					 # Formatted date string (YYYY-MM-DD)
			"time_utc": str					  # ISO 8601 timestamp
		},
		...
	]

Example:
	>>> from fomc_calendar import get_next_meeting_time, get_all_meetings
	>>> next_meeting = get_next_meeting_time()
	>>> print(next_meeting)
	2026-03-18 18:00:00+00:00

	>>> all_meetings = get_all_meetings()
	>>> for meeting in all_meetings:
	...	 print(f"{meeting['date_str']}: {meeting['time_utc']}")
	2026-01-28: 2026-01-28T19:00:00Z
	2026-03-18: 2026-03-18T18:00:00Z
	2026-05-06: 2026-05-06T18:00:00Z
	2026-06-17: 2026-06-17T18:00:00Z
	2026-07-29: 2026-07-29T18:00:00Z
	2026-09-16: 2026-09-16T18:00:00Z
	2026-11-04: 2026-11-04T19:00:00Z
	2026-12-16: 2026-12-16T19:00:00Z

Use Cases:
	- Calculate days until next FOMC meeting for event risk assessment
	- Build FOMC meeting event study datasets for market reaction analysis
	- Schedule trading system pauses around FOMC announcement volatility
	- Track FOMC meeting frequency for monetary policy cycle analysis
	- Combine with FedWatch probabilities for comprehensive meeting preview
	- Filter economic data to pre/post FOMC periods for policy impact studies

Notes:
	- No API key required (static calendar data)
	- No rate limits (local computation)
	- Data source: Federal Reserve official calendar (manually updated annually)
	- Meeting times: 2:00 PM ET (18:00-19:00 UTC depending on DST)
	- FOMC meetings: 8 scheduled meetings per year (typically every 6-7 weeks)
	- Calendar updates: Requires manual update for new calendar years
	- Time zone: All times stored and returned in UTC for consistency
	- Meeting duration: Typically 2 days, decision announced on day 2 at 2:00 PM ET

See Also:
	- fed/fedwatch.py: Market-implied rate change probabilities for next meeting
	- fred/rates.py: Fed Funds rate data and historical policy changes
	- analysis/event_study.py: FOMC meeting event study analysis
"""

from datetime import datetime, timezone
from typing import Optional

# FOMC meeting dates for 2026 (UTC)
MEETING_CALENDAR = [
	"2026-01-28T19:00:00Z",
	"2026-03-18T18:00:00Z",
	"2026-05-06T18:00:00Z",
	"2026-06-17T18:00:00Z",
	"2026-07-29T18:00:00Z",
	"2026-09-16T18:00:00Z",
	"2026-11-04T19:00:00Z",
	"2026-12-16T19:00:00Z",
]


def get_next_meeting_time(current_time: Optional[datetime] = None) -> datetime:
	"""Get the timestamp of the next upcoming FOMC meeting.

	Args:
		current_time: Current time (defaults to now)

	Returns:
		Next FOMC meeting datetime (UTC)

	Raises:
		ValueError: If no future meeting date is found
	"""
	if current_time is None:
		current_time = datetime.now(timezone.utc)

	for meeting_str in MEETING_CALENDAR:
		meeting_time = datetime.fromisoformat(meeting_str.replace("Z", "+00:00"))

		# First meeting strictly after current time
		if meeting_time > current_time:
			return meeting_time

	raise ValueError("No upcoming FOMC meeting date found in calendar")


def get_all_meetings() -> list[dict]:
	"""Get all scheduled FOMC meetings.

	Returns:
		List of meetings with datetime and formatted date string
	"""
	meetings = []
	for meeting_str in MEETING_CALENDAR:
		meeting_time = datetime.fromisoformat(meeting_str.replace("Z", "+00:00"))
		meetings.append({"datetime": meeting_time, "date_str": meeting_time.strftime("%Y-%m-%d"), "time_utc": meeting_str})

	return meetings
