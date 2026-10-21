---
name: publish-analyze
description: Schedule approved videos via Metricool and review performance after 24h.
---

1. Get best posting times with Metricool's best-time tool for YouTube.
2. Create the scheduled post as a draft for review first (createScheduledPostForReview); the human approves before it goes live.
3. After 24h and 72h: pull analytics (views, retention, subs, link clicks). Write findings to `output/analytics/`.
4. Rank hooks/topics. Rule: remix the top 20% in the next batch, drop the bottom 50%.
