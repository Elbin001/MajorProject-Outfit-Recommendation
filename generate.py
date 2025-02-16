import sys
from diffusers import StableDiffusionPipeline
import torch

# Load the pre-trained model
pipe = StableDiffusionPipeline.from_pretrained("runwayml/stable-diffusion-v1-5", torch_dtype=torch.float16)
pipe = pipe.to("cuda")  # Move the model to GPU

# Get the prompt from command-line arguments
if len(sys.argv) > 1:
    prompt = sys.argv[1]
else:
    prompt = "A casual outfit for a woman with an hourglass body shape, medium skin tone, and oval face shape"

# Generate the image
image = pipe(prompt).images[0]

# Save the image in the static folder so it can be displayed on the web
image.save("static/generated_outfit.png")