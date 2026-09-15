import json
from pathlib import Path
import requests

def fetch_sample_data():
    url = "https://jsonplaceholder.typicode.com/posts/1"
    print(f"Fetching data from {url}...")
    response = requests.get(url)

    print(f"Status Code: {response.status_code}")

    if response.status_code == 200:
        data = response.json()

        raw_dir = Path("data/raw")
        raw_dir.mkdir(parents=True, exist_ok=True)

        file_path = raw_dir / "sample_post.json"

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f)

        print(f"\n✅ Data save successfull: {file_path}")
        return data
    else:
        print(f"❌ Failed to fetch data. Status: {response.status_code}")
        return None

if __name__ == "__main__":
    fetch_sample_data()