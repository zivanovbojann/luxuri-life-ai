
import os
import random
from datetime import datetime

os.makedirs("videos", exist_ok=True)

ideas = [
    ("BMW M5", "Work in silence. Let success make the noise."),
    ("Mercedes AMG", "Build your dream life."),
    ("Porsche 911", "Freedom is the real luxury."),
    ("Luxury cars", "Dream big. Work hard."),
    ("Night drive", "Your future starts today."),
    ("Success", "Never stop chasing your dreams.")
]

random.shuffle(ideas)
today = datetime.now().strftime("%Y-%m-%d")

for number, (topic, quote) in enumerate(ideas[:3], start=1):
    filename = f"videos/idea_{today}_{number}.txt"

    with open(filename, "w", encoding="utf-8") as file:
        file.write(f"Topic: {topic}\n")
        file.write(f"Quote: {quote}\n")

    print(f"Created: {filename}")

print("Luxury Life AI finished successfully!")
