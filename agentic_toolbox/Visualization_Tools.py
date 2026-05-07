import pandas as pd
import json
from wordcloud import WordCloud
import matplotlib.pyplot as plt

# from Office_Toolbox.Tools import Directory_Tools
# dir_tools = Directory_Tools()
# Sample data



# Load the JSON file into a DataFrame
with open('models_info.json', 'r') as json_file:
    data = json.load(json_file)

# Convert the JSON data to a DataFrame
df = pd.DataFrame.from_dict(data, orient='index')

# Combine all supported generation methods into a single string
supported_gen_methods_text = " ".join(df['supported_generation_methods'].dropna().astype(str))

# Create a word cloud for supported generation methods
wordcloud_gen_methods = WordCloud(width=800, height=400, background_color='white').generate(supported_gen_methods_text)

# Display the word cloud for supported generation methods
plt.figure(figsize=(10, 5))
plt.imshow(wordcloud_gen_methods, interpolation='bilinear')
plt.axis('off')  # Turn off axis
plt.title('Supported Generation Methods')
plt.show()

# Combine all descriptions into a single string
descriptions_text = " ".join(df['description'].dropna().astype(str))

# Create a word cloud for descriptions
wordcloud_descriptions = WordCloud(width=800, height=400, background_color='white').generate(descriptions_text)

# Display the word cloud for descriptions
plt.figure(figsize=(10, 5))
plt.imshow(wordcloud_descriptions, interpolation='bilinear')
plt.axis('off')  # Turn off axis
plt.title('Model Descriptions')
plt.show()