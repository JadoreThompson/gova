"""Hard-coded Discord message corpus for the performance tests.

The corpus models three days of activity in a single channel. Every day has a
two-hour window (18:00-20:00 UTC) during which three conversations run in
parallel, for a total of 120 messages per day and 360 messages overall.

Engagement is intentionally uneven across the days:

* day 1 - dave dominates (37 msgs), alice/bob/carol hover around 21, erin is
  the quietest.
* day 2 - erin/bob/carol drive the conversation, dave drops to 11 messages.
* day 3 - dave/erin are the most active again, bob/carol mostly listen.

Message ids are deterministic: ``10_000_000 + day * 100_000 + thread * 10_000
+ index``. Replies only ever point at an earlier message in the same thread.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

GUILD_ID = 1495532119265513513
CHANNEL_ID = 900000000000000001

DAY_COUNT = 3
CONVERSATION_MINUTES = 120
FIRST_DAY = datetime(2026, 3, 2, 18, 0, tzinfo=UTC)

USERS: dict[str, int] = {
    "alice": 100000000000000001,
    "bob": 100000000000000002,
    "carol": 100000000000000003,
    "dave": 100000000000000004,
    "erin": 100000000000000005,
}


@dataclass(frozen=True)
class MockMessage:
    id: int
    user_id: int
    content: str
    created_at: datetime
    reply_to: int | None = None
    channel_id: int = CHANNEL_ID


@dataclass(frozen=True)
class Thread:
    start_minute: int
    cadence_minutes: int
    turns: tuple[tuple[str, str] | tuple[str, str, int], ...]


DAY_THREADS: dict[int, tuple[Thread, ...]] = {
    0: (
        Thread(
            start_minute=0,
            cadence_minutes=2,
            turns=(
                ("alice", "game night tonight? thinking 8pm"),
                ("bob", "I'm in. what are we playing?", 0),
                ("carol", "count me in too"),
                ("alice", "maybe the new co-op one"),
                ("dave", "I can join after 8:30"),
                ("bob", "8:30 works better for me too"),
                ("carol", "same, 8:30 is perfect", 1),
                ("alice", "ok locking 8:30"),
                ("erin", "I might be late but I'll try"),
                ("bob", "what's the player limit?"),
                ("alice", "four player co-op"),
                ("dave", "then we need one more if erin is late"),
                ("carol", "I can grab a friend"),
                ("alice", "please do"),
                ("bob", "voice chat or text?"),
                ("carol", "voice obviously", 2),
                ("dave", "my mic is broken though"),
                ("alice", "text is fine for dave"),
                ("erin", "I can relay callouts in text"),
                ("bob", "lol okay"),
                ("carol", "we should set a channel"),
                ("alice", "I'll make one", 14),
                ("dave", "thanks"),
                ("erin", "what time zone are we using?"),
                ("alice", "server time, so 8:30 utc"),
                ("bob", "got it"),
                ("carol", "I'll be there", 25),
                ("dave", "same"),
                ("erin", "trying my best"),
                ("alice", "if anyone needs the rules I'll pin them"),
                ("bob", "please pin them"),
                ("carol", "yes please"),
                ("alice", "done"),
                ("dave", "reading now"),
                ("erin", "looks fun"),
                ("bob", "can we do a practice round?", 3),
                ("alice", "sure, 15 min warmup"),
                ("carol", "perfect"),
                ("dave", "see you all at 8:30"),
                ("erin", "later!"),
            ),
        ),
        Thread(
            start_minute=20,
            cadence_minutes=2,
            turns=(
                ("dave", "quick python question"),
                ("erin", "shoot", 0),
                ("dave", "asyncio.gather vs taskgroup?"),
                ("erin", "taskgroup is newer, structured"),
                ("alice", "taskgroup also cancels siblings on error", 3),
                ("dave", "so taskgroup is safer?"),
                ("erin", "generally yes for new code"),
                ("alice", "agreed"),
                ("dave", "does it work in 3.13?"),
                ("erin", "yes, it's been there since 3.11"),
                ("dave", "nice"),
                ("alice", "watch out for exceptions in child tasks", 10),
                ("dave", "how so?"),
                ("alice", "they propagate as ExceptionGroup"),
                ("erin", "which you can catch with except*"),
                ("dave", "oh right"),
                ("erin", "if you need partial results use gather(return_exceptions=True)"),
                ("dave", "good to know"),
                ("alice", "depends if you want fail-fast or not", 14),
                ("dave", "I want fail-fast"),
                ("erin", "then taskgroup"),
                ("dave", "thanks both"),
                ("alice", "anytime"),
                ("erin", "also check timeout context manager", 16),
                ("dave", "asyncio.timeout?"),
                ("erin", "yes"),
                ("alice", "wraps the whole group nicely"),
                ("dave", "I'll try that"),
                ("erin", "ping me if it breaks"),
                ("dave", "will do"),
                ("alice", "what are you building?"),
                ("dave", "a small scraper"),
                ("erin", "rate limit it"),
                ("dave", "yeah with a semaphore"),
                ("alice", "classic", 32),
                ("erin", "and retries with backoff"),
                ("dave", "adding that too"),
                ("alice", "sounds solid"),
                ("dave", "thanks again"),
                ("erin", "np"),
            ),
        ),
        Thread(
            start_minute=40,
            cadence_minutes=2,
            turns=(
                ("bob", "what's everyone listening to?"),
                ("carol", "lo-fi while working"),
                ("dave", "synthwave here", 0),
                ("bob", "nice, any playlist?"),
                ("carol", "I'll drop a link"),
                ("dave", "please"),
                ("carol", "sent in general", 5),
                ("bob", "checking"),
                ("dave", "good stuff"),
                ("bob", "this one slaps"),
                ("carol", "right?"),
                ("dave", "adding to my rotation", 10),
                ("bob", "any live shows coming up?"),
                ("carol", "there's one next month"),
                ("dave", "where?"),
                ("carol", "downtown venue"),
                ("bob", "tickets pricey?"),
                ("carol", "not too bad"),
                ("dave", "I'm tempted"),
                ("bob", "same"),
                ("carol", "we could go together"),
                ("dave", "group outing", 20),
                ("bob", "I'm in"),
                ("carol", "I'll check dates"),
                ("dave", "keep us posted"),
                ("bob", "what genre is it?"),
                ("carol", "electronic mostly"),
                ("dave", "perfect"),
                ("bob", "I need new headphones first"),
                ("carol", "lol same"),
                ("dave", "mine died last week"),
                ("bob", "rip"),
                ("carol", "any recommendations?"),
                ("dave", "I got a cheap pair, works fine", 28),
                ("bob", "brand?"),
                ("dave", "I'll dm you"),
                ("carol", "me too please"),
                ("dave", "sure"),
                ("bob", "thanks"),
                ("carol", "you're the best"),
            ),
        ),
    ),
    1: (
        Thread(
            start_minute=0,
            cadence_minutes=2,
            turns=(
                ("bob", "standup in 10"),
                ("carol", "on my way", 0),
                ("erin", "joining"),
                ("alice", "can't make it, notes please"),
                ("bob", "no problem"),
                ("carol", "I'll take notes"),
                ("erin", "what's on the agenda?", 5),
                ("bob", "the api refactor"),
                ("carol", "and the migration script"),
                ("erin", "I finished the script yesterday"),
                ("bob", "nice"),
                ("carol", "any blockers?"),
                ("erin", "just one edge case", 9),
                ("bob", "details?"),
                ("erin", "nulls in legacy rows"),
                ("carol", "we can default them"),
                ("erin", "that changes semantics though"),
                ("bob", "maybe log and skip"),
                ("erin", "that works"),
                ("carol", "I'll update the ticket"),
                ("bob", "thanks"),
                ("alice", "reading notes later"),
                ("erin", "I'll write up the edge case"),
                ("bob", "appreciated", 22),
                ("carol", "next: deployment window"),
                ("bob", "Thursday night?"),
                ("erin", "works for me"),
                ("alice", "Thursday is fine"),
                ("carol", "locking it"),
                ("bob", "who's on call?", 25),
                ("erin", "I can be"),
                ("carol", "I'll back you up"),
                ("bob", "great"),
                ("alice", "I'll prep the rollback plan"),
                ("erin", "thank you"),
                ("carol", "let's keep it small"),
                ("bob", "agreed, one change at a time"),
                ("erin", "no big bangs"),
                ("alice", "classic advice"),
                ("carol", "meeting done, thanks all"),
            ),
        ),
        Thread(
            start_minute=20,
            cadence_minutes=2,
            turns=(
                ("erin", "heads up, someone dm'd me a weird link"),
                ("dave", "don't click it", 0),
                ("bob", "what did it say?"),
                ("erin", "free nitro, obviously fake"),
                ("carol", "report it"),
                ("dave", "yeah, block and report"),
                ("erin", "already did", 4),
                ("bob", "thanks for the warning"),
                ("carol", "we should pin a warning"),
                ("dave", "good idea"),
                ("erin", "I'll ask a mod"),
                ("bob", "they're usually quick", 10),
                ("carol", "meanwhile nobody click"),
                ("dave", "obviously"),
                ("erin", "the link looks like discord but isn't"),
                ("bob", "classic phishing"),
                ("carol", "scary how common it is"),
                ("dave", "stay safe everyone"),
                ("erin", "also enable 2fa"),
                ("bob", "already on", 18),
                ("carol", "same"),
                ("dave", "I should turn mine on"),
                ("erin", "do it now"),
                ("dave", "doing it"),
                ("bob", "good"),
                ("carol", "anyone else get dm'd?"),
                ("erin", "two people so far"),
                ("dave", "I didn't"),
                ("bob", "me neither"),
                ("carol", "let's compare notes later"),
                ("erin", "sure"),
                ("dave", "mod replied?", 10),
                ("erin", "yes, they're handling it"),
                ("bob", "nice"),
                ("carol", "thanks erin"),
                ("dave", "appreciate the heads up"),
                ("erin", "no problem"),
                ("bob", "community watch"),
                ("carol", "love to see it"),
                ("dave", "same"),
            ),
        ),
        Thread(
            start_minute=40,
            cadence_minutes=2,
            turns=(
                ("alice", "thinking of a community AMA"),
                ("erin", "that'd be fun"),
                ("carol", "who would host?"),
                ("alice", "maybe a rotating host", 0),
                ("erin", "I can do the first one"),
                ("carol", "I'll help with questions"),
                ("bob", "I can handle tech"),
                ("alice", "perfect team"),
                ("erin", "date?"),
                ("alice", "next weekend?"),
                ("carol", "Saturday works", 9),
                ("bob", "Sunday better for me"),
                ("erin", "let's do Saturday"),
                ("bob", "I'll make it work"),
                ("alice", "Saturday it is"),
                ("carol", "I'll draft the announcement"),
                ("erin", "and I'll prep talking points"),
                ("bob", "streaming setup?"),
                ("alice", "we have the stage channel", 16),
                ("bob", "audio test beforehand"),
                ("erin", "good call"),
                ("carol", "I'll schedule a dry run"),
                ("alice", "thanks"),
                ("bob", "what topics?"),
                ("erin", "roadmap and q&a"),
                ("carol", "maybe a demo"),
                ("alice", "demo would be great"),
                ("bob", "I can screen share", 24),
                ("erin", "let's keep it under an hour"),
                ("carol", "agreed"),
                ("alice", "I'll write the outline"),
                ("erin", "send it to us", 30),
                ("bob", "for review"),
                ("carol", "yes"),
                ("alice", "will do tonight"),
                ("erin", "looking forward"),
                ("bob", "same"),
                ("carol", "this will be good"),
                ("alice", "thanks everyone"),
                ("erin", "excited"),
            ),
        ),
    ),
    2: (
        Thread(
            start_minute=0,
            cadence_minutes=2,
            turns=(
                ("dave", "great event yesterday"),
                ("erin", "thanks! turnout was good"),
                ("alice", "the demo was smooth", 1),
                ("dave", "audio was crisp too"),
                ("erin", "bob did a great job"),
                ("alice", "we should do it monthly"),
                ("dave", "agreed"),
                ("erin", "I'll draft a schedule"),
                ("alice", "and a feedback form"),
                ("dave", "good idea", 8),
                ("erin", "what questions stood out?"),
                ("alice", "the one about performance"),
                ("dave", "we should benchmark"),
                ("erin", "I'll add that to the backlog"),
                ("alice", "nice"),
                ("dave", "also the docs question"),
                ("erin", "docs are thin, fair point"),
                ("alice", "I can help update them", 16),
                ("dave", "I'll review"),
                ("erin", "team effort"),
                ("alice", "when's the next one?"),
                ("erin", "first weekend of next month"),
                ("dave", "works"),
                ("alice", "same"),
                ("erin", "I'll post a poll for topics"),
                ("dave", "good", 22),
                ("alice", "let's include a beginner session"),
                ("erin", "love that"),
                ("dave", "mentorship angle"),
                ("alice", "exactly"),
                ("erin", "I'll reach out to volunteers"),
                ("dave", "I can mentor", 30),
                ("alice", "me too"),
                ("erin", "amazing"),
                ("dave", "let's keep momentum"),
                ("alice", "agreed"),
                ("erin", "thanks both"),
                ("dave", "anytime"),
                ("alice", "see you around"),
                ("erin", "later"),
            ),
        ),
        Thread(
            start_minute=20,
            cadence_minutes=2,
            turns=(
                ("dave", "honestly that take is bad"),
                ("bob", "which one?", 0),
                ("dave", "the one about the new feature"),
                ("bob", "it's just an opinion"),
                ("dave", "an opinion can still be wrong"),
                ("erin", "let's keep it civil"),
                ("bob", "I'm not being uncivil", 4),
                ("dave", "neither am I"),
                ("carol", "tone check both of you"),
                ("dave", "fair"),
                ("bob", "yeah, fair"),
                ("erin", "we can disagree without the edge", 10),
                ("dave", "you're right"),
                ("bob", "sorry if it came off harsh"),
                ("dave", "same here", 13),
                ("erin", "appreciated"),
                ("carol", "back to the feature"),
                ("bob", "it has real tradeoffs"),
                ("dave", "agreed, but the default is odd"),
                ("erin", "what would you change?", 18),
                ("dave", "make it opt-in"),
                ("bob", "that's reasonable"),
                ("carol", "I'd support that"),
                ("erin", "worth proposing"),
                ("dave", "I'll write it up"),
                ("bob", "I'll add my concerns"),
                ("carol", "constructive now"),
                ("erin", "nice recovery", 26),
                ("dave", "lol"),
                ("bob", "teamwork"),
                ("carol", "see, this is better"),
                ("erin", "much"),
                ("dave", "agreed"),
                ("bob", "any other topics?"),
                ("carol", "release notes"),
                ("erin", "I'll draft them"),
                ("dave", "thanks"),
                ("bob", "appreciate it"),
                ("carol", "good chat"),
                ("erin", "later all"),
            ),
        ),
        Thread(
            start_minute=40,
            cadence_minutes=2,
            turns=(
                ("erin", "weekend plans?"),
                ("carol", "hiking if weather holds"),
                ("dave", "sounds nice"),
                ("alice", "I'm staying in"),
                ("erin", "movie marathon?"),
                ("alice", "yes", 0),
                ("carol", "count me in for one night"),
                ("dave", "what movies?"),
                ("erin", "sci-fi classics"),
                ("alice", "blade runner"),
                ("carol", "obviously", 9),
                ("dave", "I haven't seen it"),
                ("erin", "what?!"),
                ("alice", "you're in for a treat"),
                ("dave", "adding to list"),
                ("carol", "start with the original"),
                ("erin", "and then 2049"),
                ("dave", "noted"),
                ("alice", "popcorn ready", 16),
                ("carol", "I'll bring snacks"),
                ("dave", "I'll bring drinks"),
                ("erin", "I'll host"),
                ("alice", "perfect"),
                ("carol", "time?"),
                ("erin", "Saturday 7pm"),
                ("dave", "works"),
                ("alice", "same"),
                ("carol", "I'll be there", 24),
                ("erin", "no spoilers please"),
                ("dave", "I know nothing"),
                ("alice", "good"),
                ("erin", "trailer?"),
                ("dave", "maybe just one"),
                ("alice", "no trailer, go in blind"),
                ("carol", "agreed"),
                ("erin", "excited", 30),
                ("dave", "fine"),
                ("carol", "see you saturday"),
                ("alice", "me too"),
                ("erin", "later"),
            ),
        ),
    ),
}


def _build() -> list[MockMessage]:
    messages: list[MockMessage] = []
    for day_index, threads in DAY_THREADS.items():
        day_start = FIRST_DAY + timedelta(days=day_index)
        for thread_index, thread in enumerate(threads):
            base_id = 10_000_000 + day_index * 100_000 + thread_index * 10_000
            thread_ids = [base_id + index for index in range(len(thread.turns))]
            for index, turn in enumerate(thread.turns):
                user_key, content = turn[0], turn[1]
                reply_index = turn[2] if len(turn) > 2 else None
                messages.append(
                    MockMessage(
                        id=thread_ids[index],
                        user_id=USERS[user_key],
                        content=content,
                        created_at=day_start
                        + timedelta(
                            minutes=thread.start_minute + index * thread.cadence_minutes
                        ),
                        reply_to=thread_ids[reply_index]
                        if reply_index is not None
                        else None,
                        channel_id=CHANNEL_ID + day_index,
                    )
                )
    messages.sort(key=lambda message: (message.created_at, message.id))
    return messages


MOCK_MESSAGES: list[MockMessage] = _build()


def messages_for_day(day_index: int) -> list[MockMessage]:
    channel_id = CHANNEL_ID + day_index
    return [message for message in MOCK_MESSAGES if message.channel_id == channel_id]


def sample_messages(limit: int) -> list[MockMessage]:
    """Return ``limit`` messages spread evenly across the whole corpus."""

    if limit >= len(MOCK_MESSAGES):
        return list(MOCK_MESSAGES)
    if limit <= 0:
        return []

    step = len(MOCK_MESSAGES) / limit
    return [MOCK_MESSAGES[int(index * step)] for index in range(limit)]
