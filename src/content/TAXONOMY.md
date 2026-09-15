# Appearance taxonomy

The exact words. Every entry in `appearances.yaml` uses these and only these.
The build fails on anything else, so the vocabulary cannot drift.

## The rule that prevents most inconsistency

**`title` is the name of the thing, and nothing else.** Not the role, not the
format, not the venue. Those are fields.

    WRONG   title: 'Podcast Guest: Data, Misaligned; Bad Data Ruins AI'
    RIGHT   title: 'Data, Misaligned; Bad Data Ruins AI'
            role: guest

If a prefix in a title tells you something a field already records, delete the
prefix. This is the failure that makes a list of appearances look like three
different lists.

## kind

| value     | means                                        |
| --------- | -------------------------------------------- |
| `talk`    | she presented at an event                    |
| `podcast` | an episode of a show, hers or someone else's |

## talk fields

**`eventType`** — the shape of the slot, not the content.

| value      | means                                                       |
| ---------- | ----------------------------------------------------------- |
| `talk`     | she presented. Slides, demo, or both — all still a talk.     |
| `keynote`  | the named keynote slot                                       |
| `panel`    | multi-person discussion, no single presenter                 |
| `workshop` | hands-on, participants do the work                           |

A demo is not an event type. A talk with a demo is a `talk`; tag it `demo` if
that matters for a given talk.

**`location`** — city, or `virtual`. Not the venue name; that is `org`.

## podcast fields

**`role`** — which chair she was in.

| value        | means                                                         |
| ------------ | ------------------------------------------------------------- |
| `guest`      | she answered the questions                                     |
| `guest host` | she asked the questions, on someone else's show                |
| `co-host`    | she shared the chair for an episode                            |
| `panelist`   | several voices, no single interviewer                          |

"Itinerant podcaster" is how she describes the body of this work. It is a page
headline, not a field value.

**`format`** — `live` or `recorded`. Determined by how it was captured, not how
you watch it now. A YouTube URL containing `/live/` was a live stream.

**`counterpart`** — who she interviewed. Only when `role` is `guest host`.

## shared fields

| field    | notes                                                          |
| -------- | -------------------------------------------------------------- |
| `id`     | kebab-case, unique, stable. Never renamed once published.        |
| `date`   | `YYYY-MM-DD`. Release date for podcasts, event date for talks.   |
| `org`    | the show or event, spelled one way everywhere. See below.        |
| `url`    | canonical link. One per episode — see canonical URLs.            |
| `note`   | anything true that no field holds.                               |
| `tags`   | lowercase, kebab-case, reused across entries.                    |

## org names — spelled one way

These are the exact strings. A show renamed here is a show that splits into two
in every count that groups by `org`.

- `AI Tinkerers Toronto`
- `Agile Data Podcast`
- `Canadian Women in Cybersecurity`
- `Christopher Gambill`
- `Data Engineering & ML Summit`
- `Data Podcast for Nerds!`
- `Data in the D`
- `LEIT Data Podcast`
- `Neo4j NODES`
- `Super Data Show`
- `The Data Engineering Channel`
- `The Data Intelligence Platform`

## canonical URLs

One link per episode, in one form:

- YouTube video: `https://www.youtube.com/watch?v=ID` — no `&t=`, no `youtu.be`
- YouTube live: `https://www.youtube.com/live/ID`
- anything else: the publisher's own permalink

The same video written two ways is the same duplicate problem as the same show
spelled two ways.

## visibility — derived, never stored

There is no status field to keep current.

- **talks** always render; upcoming versus past comes from `date`
- **podcasts** render once they have a `url`

To publish an episode, paste its link. That is the whole workflow.
