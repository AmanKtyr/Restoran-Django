from PIL import Image, ImageDraw, ImageFont
import os

# Create the directory if it doesn't exist
os.makedirs('static/img', exist_ok=True)

# List of image names we need
image_names = [
    ('hero.png', (800, 600)),
    ('about-1.jpg', (600, 400)),
    ('about-2.jpg', (600, 400)),
    ('about-3.jpg', (600, 400)),
    ('about-4.jpg', (600, 400)),
    ('team-1.jpg', (300, 300)),
    ('team-2.jpg', (300, 300)),
    ('team-3.jpg', (300, 300)),
    ('team-4.jpg', (300, 300)),
    ('testimonial-1.jpg', (300, 300)),
    ('testimonial-2.jpg', (300, 300)),
    ('testimonial-3.jpg', (300, 300)),
    ('testimonial-4.jpg', (300, 300)),
    ('menu-1.jpg', (600, 400)),
    ('bg-hero.jpg', (800, 600)),
    ('video.jpg', (600, 400)),
    ('favicon.ico', (32, 32)),
]

# Create placeholder images
for img_name, size in image_names:
    # Create a new image with a color
    img = Image.new('RGB', size, color=(73, 109, 137))
    
    # Get a drawing context
    d = ImageDraw.Draw(img)
    
    # Draw text on the image
    text = img_name
    # Calculate text position to center it
    text_width = len(text) * 10  # Approximate width
    text_x = (size[0] - text_width) // 2
    text_y = size[1] // 2 - 10
    
    d.text((text_x, text_y), text, fill=(255, 255, 255))
    
    # Save the image
    img_path = os.path.join('static/img', img_name)
    img.save(img_path)
    print(f'Created {img_name}')

print('All images created successfully!')
