# Post-launch adoption plan

The adoption objective is real use, not version churn. Do not publish another large version immediately after launch.

Capture at launch, about 7 days, about 14 days, and about 30 days:

- views
- downloads
- votes
- public/external notebook count when available
- discussion/comment signals when available
- current version/update date
- usability rating

Diagnose the funnel rather than treating a single vote count as success/failure:

- **Low views**: improve title/subtitle/cover/tags/discoverability before changing the data.
- **Views but few downloads**: clarify the first use case and verify file-choice/size friction.
- **Downloads but few votes**: strengthen distinctiveness, notebook insight, and product explanation.
- **Only creator notebook reuse**: make examples easier to reuse; do not add duplicate file formats.
- **External notebooks/comments appear**: stabilize the schema and prioritize predictable monthly refreshes.
- **Usability 10/10 but weak engagement**: stop metadata micro-optimization and revisit product-market fit.

Each checkpoint should be persisted under `state/adoption/` locally and compared with the closest direct SGO alternative as well as the broader crash-data analogs recorded in `research/market_analogs.csv`.
