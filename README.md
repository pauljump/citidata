# citidata

Downloads and verifies monthly Citi Bike trip data. The trip data itself is not in this repo.

```bash
python3 fetch.py --dest "/Volumes/Backup Plus/citibike" --list
python3 fetch.py --dest "/Volumes/Backup Plus/citibike"
```

It fetches the newest 6 months by default (`--months N` to change) from the official bucket,
https://s3.amazonaws.com/tripdata, with one folder per month and region: `nyc-202610/`, `jc-202610/`
(Jersey City and Hoboken). Needs Python 3.8+ and curl. Existing complete files are kept.

`manifest.json` records size, SHA-256, trip count and first/last start date for May through
October 2026 (12 files, 31,033,582 trips).

## Notes on the data

- Monthly files can include trips that started in the last day or two of the previous month.
  Filter on `started_at` for clean months.
- The October 2026 NYC file is compressed inside the zip; May through September 2026 are stored
  uncompressed, so their zip size is close to their CSV size.
- New months have been posted between the 3rd and 12th of the following month.

## Why the data is not here

The [Data License Agreement](https://citibikenyc.com/data-sharing-policy), section 2(b), does not
allow hosting or distributing the data as a stand-alone dataset. Each user downloads it from the
official source. This project is not affiliated with or endorsed by Citi Bike, Lyft or Citigroup.
