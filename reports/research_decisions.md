# Research Decisions

## Keep the sector baseline, but exclude it from final spectral selection

The sector-neutral sleeve is useful context, but it should not answer the spectral question for us. Final public selection is restricted to the spectral sleeves.

## Use a deliberately naive raw PCA comparison

The raw PCA sleeve is intentionally fixed-rank. The point is to compare that common research shortcut with data-driven spectral rank selection.

## Stabilize the RMT sleeve with the same portfolio controls used elsewhere

The public RMT sleeves use the same beta-neutral and turnover-aware portfolio construction rules as the rest of the repo. The signal is not presented as tradable in isolation.

## Leave cost fragility visible

The selected sleeve looks strong at `1` bp and much weaker by `10` bps. That stays in the repo because it is part of the real research story.
