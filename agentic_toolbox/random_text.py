import random

# Expanded list of topics
topics = [
    "Technology", "Sports", "Science", "History", "Entertainment", "Health",
    "Food", "Vegetables", "Microscopy", "Astronomy", "Marine Biology", "Literature",
    "Mathematics", "Artificial Intelligence", "Climate Change", "Architecture", 
    "Psychology", "Physics", "Education", "Fashion", "Economics", "Gardening",
    "Space Exploration", "Renewable Energy", "Robotics", "Genetics"
]

# Expanded list of descriptions
descriptions = [
    "Exploring the latest advancements in {}.",
    "Historical trends and their impact on {}.",
    "Analyzing the importance of {} in modern society.",
    "The evolution of {} over the decades.",
    "How {} is shaping our future.",
    "The role of {} in everyday life.",
    "Understanding the complexities of {}.",
    "A beginner's guide to {}.",
    "The challenges and opportunities in {}.",
    "The untold story of {}.",
    "How {} influences global perspectives.",
    "The connection between {} and sustainability.",
    "An in-depth look at {}.",
    "How to master {}: Tips and techniques.",
    "Why {} matters in today's world.",
    "The future of {} in the next decade.",
    "The relationship between {} and human behavior.",
    "Unveiling the mysteries of {}.",
    "Practical applications of {} in daily life.",
    "The impact of {} on economic growth.",
    "How {} intersects with creativity.",
    "The science behind {} explained.",
    "Key breakthroughs in {} research.",
    "The art and science of {}.",
    "How {} can improve quality of life."
]

# Generate random data
with open("test_data.txt", "w") as file:
    for i in range(100):  # Generate 100 entries
        topic = random.choice(topics)
        description = random.choice(descriptions).format(topic)
        metadata = f"ID-{i+1}, Tag: {topic}"
        file.write(f"{description} | {metadata}\n")

print("test_data.txt")
