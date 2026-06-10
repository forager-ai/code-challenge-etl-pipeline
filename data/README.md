# Data

Download the data bundle (`forager-takehome-data.zip`, ~1 GB):

**[https://drive.google.com/file/d/1EdnlIxk615H36rDw5NmLt_s-P4EK_0na/view?usp=sharing](https://drive.google.com/file/d/1EdnlIxk615H36rDw5NmLt_s-P4EK_0na/view?usp=sharing)**

Unzip it into this directory. After extracting, the layout is:

```
data/
├── person/
│   └── data_0_N_0.json.gz       # 8 files, 1,000,000 person records total
└── organization/
    └── data_0_N_0.json.gz       # 8 files, ~529,000 organization records total
```

The pipeline container mounts this directory at `/data` (read-only).

> **The files are NDJSON despite the `.json.gz` extension** — one JSON document
> per line. Don't try to `json.load()` the whole file; stream it line-by-line.

## Record shapes

Records follow Forager's real data-feed format
([Person feed v2](https://docs.forager.ai/data-license/v2/schema#person-data-feed),
[Organization feed v2](https://docs.forager.ai/data-license/v2/schema#organization-data-feed)).
Every record is wrapped in an envelope; the rich content lives inside
`serialized_data`.

### Person record (envelope)

```json
{
  "id": 582216891,
  "date_updated": "2026-03-29 02:32:15.041 Z",
  "serialized_data": { /* rich person object — see below */ }
}
```

`id` and `serialized_data.forager_id` are the same value.

### `person.serialized_data` (observed fields)

```json
{
  "forager_id": 582216891,
  "linkedin_id": 1599488000,
  "date_updated": "2026-03-29 02:32:15.459 Z",
  "first_name": "...",
  "last_name": "...",
  "headline": "...",
  "country": "...",
  "area": "...",
  "city": "...",
  "location": "...",
  "locations": [ /* ... */ ],
  "industry": "...",
  "linkedin_url": "https://...",
  "linkedin_slug": "...",
  "linkedin_country": "...",
  "linkedin_area": "...",
  "number_of_connections": 412,
  "number_of_followers": 1280,
  "is_available": true,
  "skills": ["..."],
  "volunteer_causes": [],
  "roles": [
    {
      "id": 1217254644,
      "linkedin_id": 1599488461,
      "role_title": "Information Technology Specialist",
      "organization_id": 140717,
      "organization_name": "Dell Technologies",
      "organization_domain": "delltechnologies.com",
      "organization_industry": "Computer Hardware",
      "organization_linkedin_id": 15088102,
      "organization_linkedin_info_public_identifier": "delltechnologies",
      "organization_website": "https://delltechnologies.com/",
      "date_updated": "2026-03-29 02:32:15.459 Z"
    }
  ],
  "organizations": [],
  "educations": [], "certifications": [], "languages": [],
  "projects": [], "publications": [], "patents": [],
  "honors": [], "courses": [], "test_scores": [], "volunteering": []
}
```

> **Note:** `serialized_data.organizations` is **empty** in the input.
> Populating it is your job — see [`../README.md`](../README.md#output).
> Notice that `roles[]` already carries denormalized organization fields
> (`organization_name`, `organization_domain`, `organization_industry`, etc.),
> but the orgs feed contains additional fields (`linkedin_id`, `addresses`,
> `keywords`, `technologies`, etc.) that are not present in the role
> denormalization.

### Organization record (envelope)

```json
{
  "id": 67354352,
  "date_updated": "2026-03-17 23:53:21.125 Z",
  "serialized_data": { /* org object — see below */ }
}
```

### `organization.serialized_data` (observed fields)

```json
{
  "forager_id": 67354352,
  "linkedin_id": 112226750,
  "date_updated": "2026-03-17 23:53:21.125 Z",
  "name": "Acme",
  "addresses": [],
  "locations": [],
  "keywords": [],
  "technologies": [],
  "funding_rounds": []
}
```

> Many array fields (`addresses`, `keywords`, `technologies`, etc.) are
> commonly empty. Reliable fields for joining and indexing are `forager_id`,
> `linkedin_id`, and `name`.

## Joining persons and organizations

Each person role references its organization by **`roles[].organization_id`**,
which matches **`serialized_data.forager_id`** in the organization feed.

Not every `organization_id` will resolve against the orgs feed (some role
references point to orgs absent from the sample). Handle this gracefully —
don't crash, and don't silently drop the role.
