import { getCollection } from 'astro:content'

type Entry = Awaited<ReturnType<typeof getCollection<'appearances'>>>[number]

const byNewest = (a: Entry, b: Entry) => b.data.date.valueOf() - a.data.date.valueOf()
const byOldest = (a: Entry, b: Entry) => a.data.date.valueOf() - b.data.date.valueOf()

/** Talks, split on today's date. Upcoming runs soonest-first. */
export async function talks() {
  const all = (await getCollection('appearances')).filter((e) => e.data.kind === 'talk')
  const now = Date.now()
  return {
    upcoming: all.filter((e) => e.data.date.valueOf() >= now).sort(byOldest),
    past: all.filter((e) => e.data.date.valueOf() < now).sort(byNewest)
  }
}

/**
 * Podcasts that are actually published, split by which chair she was in.
 * An entry without a url is recorded but not out, so it stays off the site
 * until its link is pasted in. There is no status field to flip.
 */
export async function podcasts() {
  const published = (await getCollection('appearances'))
    .filter((e) => e.data.kind === 'podcast' && e.data.url)
    .sort(byNewest)
  return {
    asGuest: published.filter((e) => e.data.kind === 'podcast' && e.data.role !== 'interviewer'),
    asInterviewer: published.filter(
      (e) => e.data.kind === 'podcast' && e.data.role === 'interviewer'
    ),
    /** Recorded, no link yet — for your own eyes, not the site. */
    unpublished: (await getCollection('appearances')).filter(
      (e) => e.data.kind === 'podcast' && !e.data.url
    )
  }
}

/** Distinct shows she has appeared on — the number the résumé claims. */
export async function showCount() {
  const shows = (await getCollection('appearances'))
    .filter((e) => e.data.kind === 'podcast' && e.data.url)
    .map((e) => e.data.org)
  return new Set(shows).size
}
