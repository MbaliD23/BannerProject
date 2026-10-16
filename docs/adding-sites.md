# Adding another website

Most sites require configuration only; collector code should remain unchanged.

1. Inspect the homepage at a desktop viewport and identify the narrowest stable carousel container.
2. Add a new entry to `config/sites.yaml` with a unique lowercase `key`, display `name`, canonical `url`, and ordered selectors.
3. Put specific selectors first and generic fallbacks last. Selectors should identify the promotional carousel, not game tiles or navigation artwork.
4. Add selectors for cookie/marketing overlays to `dismiss_selectors`.
5. Run `banner-analytics collect` in staging.
6. Confirm screenshot boundaries, slide count, OCR text, click-through URLs, and Operations status.
7. Add campaign vocabulary and providers to `config/categories.yaml` without removing existing rules.

Example:

```yaml
- key: examplebet
  name: ExampleBet
  url: https://www.example.test
  enabled: true
  wait_until: networkidle
  carousel_selectors:
    - "section[data-testid='promotion-carousel']"
    - ".hero .swiper"
  slide_selectors:
    - ".swiper-slide:not(.swiper-slide-duplicate)"
  image_selectors: ["picture img", "img"]
  next_selectors: [".swiper-button-next"]
  dismiss_selectors: ["button:has-text('Accept')"]
```

If a site renders promotions inside an iframe, canvas, shadow DOM, or authenticated session, create a small adapter class that implements the same capture output contract used by `BannerCollector._capture_slides`. Keep site-specific logic isolated and add a fixture-based integration test.

## Selector maintenance

- Prefer `data-*` attributes and semantic roles over generated class names.
- Require a minimum visual size to avoid capturing icons.
- Keep multiple ordered fallbacks because layouts vary by breakpoint and anonymous/login state.
- Treat a successful run with zero captures as a failure signal, not valid data.
- Never increase retry frequency to compensate for a broken selector; update the selector instead.

