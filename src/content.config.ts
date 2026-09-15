import { defineCollection } from 'astro:content'
import { file, glob } from 'astro/loaders'
import { z } from 'astro/zod'

function removeDupsAndLowerCase(array: string[]) {
  if (!array.length) return array
  const lowercaseItems = array.map((str) => str.toLowerCase())
  const distinctItems = new Set(lowercaseItems)
  return Array.from(distinctItems)
}

// Define blog collection
const blog = defineCollection({
  // Load Markdown and MDX files in the `src/content/blog/` directory.
  loader: glob({ base: './src/content/blog', pattern: '**/*.{md,mdx}' }),
  // Required
  schema: ({ image }) =>
    z.object({
      // Required
      title: z.string().max(60),
      description: z.string().max(160),
      publishDate: z.coerce.date(),
      // Optional
      updatedDate: z.coerce.date().optional(),
      heroImage: z
        .object({
          src: image(),
          alt: z.string().optional(),
          inferSize: z.boolean().optional(),
          width: z.number().optional(),
          height: z.number().optional(),

          color: z.string().optional()
        })
        .optional(),
      tags: z.array(z.string()).default([]).transform(removeDupsAndLowerCase),
      language: z.string().optional(),
      draft: z.boolean().default(false),
      // Special fields
      comment: z.boolean().default(true)
    })
})

// Define docs collection
const docs = defineCollection({
  loader: glob({ base: './src/content/docs', pattern: '**/*.{md,mdx}' }),
  schema: () =>
    z.object({
      title: z.string().max(60),
      description: z.string().max(160),
      publishDate: z.coerce.date().optional(),
      updatedDate: z.coerce.date().optional(),
      tags: z.array(z.string()).default([]).transform(removeDupsAndLowerCase),
      draft: z.boolean().default(false),
      // Special fields
      order: z.number().default(999)
    })
})

// Every public appearance — talks and podcasts — in one file.
// The site renders it; podcast-clips reads the same file as its corpus
// manifest. Shared fields are validated once; each kind adds its own.

const appearanceBase = {
  date: z.coerce.date(),
  title: z.string(),
  org: z.string(),
  // A podcast is published once it has a url. Talks render regardless.
  url: z.string().url().optional(),
  note: z.string().optional(),
  tags: z.array(z.string()).default([]).transform(removeDupsAndLowerCase)
}

const appearances = defineCollection({
  loader: file('./src/content/appearances.yaml'),
  schema: z.discriminatedUnion('kind', [
    z.object({
      kind: z.literal('talk'),
      eventType: z.enum(['talk', 'keynote', 'panel', 'workshop']),
      location: z.string(),
      ...appearanceBase
    }),
    z.object({
      kind: z.literal('podcast'),
      // See TAXONOMY.md. "guest host" = she asked the questions on someone
      // else's show. "Itinerant podcaster" is a page headline, not a value.
      role: z.enum(['guest', 'guest host', 'co-host', 'panelist']),
      format: z.enum(['live', 'recorded']),
      // who she interviewed, only when role is "guest host"
      counterpart: z.string().optional(),
      transcript: z.string().optional(),
      ...appearanceBase
    })
  ])
})

export const collections = { blog, docs, appearances }
