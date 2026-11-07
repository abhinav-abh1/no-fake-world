# Data notes (updated 2026-11-06)

## Text extraction
- Only The Guardian - World is enabled for full text.  314 articles extracted so far,
  typically  5039 characters long.
- Quality: the extracted text starts at the article body, with no menus, cookie notices or
  "related stories" blocks (I read samples).
- Many sentences report what someone said or claimed ("suggested", "reportedly", "claimed"), so
  the claim extractor must separate "X said Y" from "Y is true".
- The other seven outlets only give a title and a feed snippet, often one or two sentences.

## Source coverage
- Eight outlets, one feed each: The Guardian, BBC, Al Jazeera, DW, France 24, The Hindu, NPR, Sky News.
- Feeds list very different numbers of items per fetch (DW 130, The Hindu 60, The Guardian 45,
  BBC 28, Al Jazeera 25, France 24 24, NPR 10, Sky 9).
- Articles published in the last 4 days (6 Nov): Al Jazeera 148, The Guardian 132, France 24 115,
  The Hindu 88, BBC 61, DW 57, Sky 9, NPR 8. Sky and NPR are 17 of 618 (2.8%).

## Collection gaps
- The collector only runs while my laptop and Docker Desktop are on. In the 73 hours up to
  4 Nov 15:00 UTC it ran in only 12 hours (gaps of 24, 11 and 19 hours); the log up to 6 Nov
  shows more gaps of about 11 hours.
- Outlets with short feeds (Sky, NPR) lose articles during gaps, so outlet counts used for
  independence are biased toward outlets with long feeds.
- Interim fixes: container restart policy, the script brings the database up and waits for it,
  the task wakes the PC. Real fix: run ingestion on a server.