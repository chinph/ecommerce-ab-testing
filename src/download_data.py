"""Download the Hillstrom E-Mail Analytics Challenge data into data/raw/.

The source gives no formal license, so the file is fetched from the author's site rather than redistributed in this repo.
"""
from pathlib import Path
from urllib.request import urlopen

URL = "http://www.minethatdata.com/Kevin_Hillstrom_MineThatData_E-MailAnalytics_DataMiningChallenge_2008.03.20.csv"
OUT = Path(__file__).resolve().parents[1] / "data" / "raw" / "hillstrom.csv"

if __name__ == "__main__":
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_bytes(urlopen(URL, timeout=60).read())
    print(f"Saved {OUT} ({OUT.stat().st_size:,} bytes)")
