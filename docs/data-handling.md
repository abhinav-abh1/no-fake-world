# Data handling rules

- We fetch full article text only from sources I enabled after reading their terms (`sources.robots_ok = true`).
- We check robots.txt before every page and stop if it cannot be read.
- Full text is stored for internal analysis only (search, claims, verification). It is never displayed or republished.
- Readers see our own cited writing, short snippets, and links to the original articles.
- The bot identifies itself (`NoFakeWorldBot`) and waits between requests.
- A takedown request from an outlet is honoured by disabling the source and deleting its stored text.