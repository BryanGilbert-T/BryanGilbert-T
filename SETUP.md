# Install the animated GitHub profile banner

Designed for https://github.com/BryanGilbert-T/BryanGilbert-T

## Replace files

1. In your profile repository on the `main` branch, **replace the root `README.md`** with the one in this package.
2. **Add** `assets/aurora.svg` with that exact path. Keep the `assets` directory.
3. Commit both files and refresh your profile page. There is no GitHub Action or API token required.

Optional cleanup if you no longer want the old candlestick setup: delete `.github/workflows/candles.yml`, `scripts/generate_candles.py`, and `assets/candles.svg`. If you previously uploaded `assets/intro.gif` and `assets/banner.svg`, those are no longer referenced by the new README either.

## Behavior

- Aurora ribbons continuously flow at different slow speeds (approximately 19–29 seconds per cycle), with seamless individual loops.
- Name and subtitle stay centered and still; each fades in once when the image loads.
- No JavaScript, external requests, paid services, or ongoing maintenance.
- All motion is in one self-contained animated SVG. A browser with disabled SVG animation will still see the static text and wave.

**Note:** GitHub caches images. After uploading, if an earlier banner appears, hard refresh or change `assets/aurora.svg` to `assets/aurora.svg?v=2` in README. SVG animation playback can vary by browser or GitHub image proxy, so check the live profile after uploading.
