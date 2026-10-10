```python
import os
import random
from datetime import datetime

OUTPUT_DIR = "videos"
os.makedirs(OUTPUT_DIR, exist_ok=True)

IDEAS = [
    ("BMW M5", "Work in silence. Let success make the noise."),
    ("Mercedes AMG", "Your future is built by what you do today."),
    ("Porsche 911", "Dream big. Work hard. Stay free."),
    ("Luxury lifestyle", "Freedom is the real luxury."),
    ("Night drive", "One day, the hard work will pay off."),
    ("Success mindset", "Build a life you don't need a vacation from."),
]

def main():
    today = datetime.now().strftime("%Y-%m-%d")
    random.shuffle(IDEAS)

    for number, (topic, quote) in enumerate(IDEAS[:3], start=1):
        filename = f"{OUTPUT_DIR}/idea_{today}_{number}.txt"

        with open(filename, "w", encoding="utf-8") as file:
            file.write(f"VIDEO {number}\n")
            file.write(f"Topic: {topic}\n")
            file.write(f"Quote: {quote}\n")
            file.write("Format: YouTube Shorts, vertical 9:16\n")
            file.write("Music: Use properly licensed music\n")

        print(f"Prepared: {filename}")

if __name__ == "__main__":
    main()
```
