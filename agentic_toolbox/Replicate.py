import os

replicate_api_token = os.getenv("REPLICATE_API_TOKEN")
if not replicate_api_token:
    raise ValueError("Set REPLICATE_API_TOKEN before running this script.")

import replicate


output = replicate.run(
    "black-forest-labs/flux-1.1-pro",
    input={
        "prompt": "Anime style image of foriegners in chennai attire celebrating Diwali with works\"Long Live Stalin\", in a banner. Consider people of swedish, mediterraean and slavic descent to populate. put them in the backdrop of a slum but they are happy with their life",
        "aspect_ratio": "1:1",
        "output_format": "webp",
        "output_quality": 80,
        "safety_tolerance": 2,
        "prompt_upsampling": True
    }
)
print(output)