from PIL import Image, ImageDraw, ImageFont
import os

# Create directory if it doesn't exist
os.makedirs('app/static/favicon', exist_ok=True)

# Create a simple favicon with text
def create_text_favicon(text, bg_color, text_color, size=512):
    # Create a square image
    img = Image.new('RGB', (size, size), color=bg_color)
    d = ImageDraw.Draw(img)
    
    # Try to use a system font, or default to a basic one
    try:
        font = ImageFont.truetype("Arial Bold.ttf", size=int(size/2))
    except IOError:
        font = ImageFont.load_default()
    
    # Calculate text position to center it
    w, h = d.textsize(text, font=font)
    position = ((size-w)/2, (size-h)/2)
    
    # Draw the text
    d.text(position, text, fill=text_color, font=font)
    
    # Save different sizes
    img.save('app/static/favicon/apple-touch-icon.png')
    
    img_32 = img.resize((32, 32))
    img_32.save('app/static/favicon/favicon-32x32.png')
    
    img_16 = img.resize((16, 16))
    img_16.save('app/static/favicon/favicon-16x16.png')
    
    # Save ico format
    img_32.save('app/static/favicon/favicon.ico')
    
    # Also create Android versions
    img_192 = img.resize((192, 192))
    img_192.save('app/static/favicon/android-chrome-192x192.png')
    img.save('app/static/favicon/android-chrome-512x512.png')
    
    print("Favicon files created successfully!")

# Create a favicon with the first letter of your app name
create_text_favicon("S", "#0d6efd", "#ffffff") 