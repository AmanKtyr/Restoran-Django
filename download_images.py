import os
import requests
from PIL import Image
from io import BytesIO

# Create the directory if it doesn't exist
os.makedirs('static/img', exist_ok=True)

# List of image names we need
image_names = [
    'hero.png',
    'about-1.jpg',
    'about-2.jpg',
    'about-3.jpg',
    'about-4.jpg',
    'team-1.jpg',
    'team-2.jpg',
    'team-3.jpg',
    'team-4.jpg',
    'testimonial-1.jpg',
    'testimonial-2.jpg',
    'testimonial-3.jpg',
    'testimonial-4.jpg',
    'menu-1.jpg',
    'bg-hero.jpg',
    'video.jpg',
]

# Download placeholder images
for img_name in image_names:
    # Get a placeholder image from placeholder.com
    size = '600x400'
    if 'hero' in img_name:
        size = '800x600'
    elif 'team' in img_name or 'testimonial' in img_name:
        size = '300x300'
    
    # Use placeholder.com to get placeholder images
    url = f'https://via.placeholder.com/{size}'
    
    try:
        response = requests.get(url)
        img = Image.open(BytesIO(response.content))
        
        # Save the image
        img_path = os.path.join('static/img', img_name)
        img.save(img_path)
        print(f'Downloaded {img_name}')
    except Exception as e:
        print(f'Error downloading {img_name}: {e}')

print('All images downloaded successfully!')
