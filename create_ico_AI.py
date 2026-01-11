"""
Script to create ChatList icon with red "AI" letters in a blue circle.
Generates icon with red text "AI" on blue circle background.
"""

from PIL import Image, ImageDraw, ImageFont
import math
import os


def load_font(size: int) -> ImageFont.FreeTypeFont:
    """
    Load an Arial-based font with fallback to default.
    """
    try:
        return ImageFont.truetype("arialbd.ttf", size)
    except:
        try:
            return ImageFont.truetype("arial.ttf", size)
        except:
            return ImageFont.load_default()


def create_ai_icon(output_ico: str = "app_ai.ico"):
    """
    Creates application icon with red "AI" letters in a blue circle.
    Letters are maximized to fill the circle while staying inside.
    
    Args:
        output_ico: Path to save ICO file
    """
    # Icon sizes for ICO file
    sizes = [(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)]
    
    # Colors
    background_color = (0, 0, 0, 0)  # Transparent background
    circle_color = (100, 180, 255)   # Blue circle
    text_color = (220, 50, 50)       # Red text
    
    images = []
    
    for size in sizes:
        width, height = size
        
        # Create image with transparent background
        img = Image.new('RGBA', (width, height), background_color)
        draw = ImageDraw.Draw(img)
        
        # Center and radius
        center_x = width // 2
        center_y = height // 2
        
        # Padding for circle
        padding = int(min(width, height) * 0.05)
        circle_radius = min(width, height) // 2 - padding
        
        # Draw blue circle
        circle_bbox = [
            center_x - circle_radius,
            center_y - circle_radius,
            center_x + circle_radius,
            center_y + circle_radius
        ]
        draw.ellipse(circle_bbox, fill=circle_color)
        
        # Draw "AI" text
        # MAXIMIZE font size to fill circle but stay inside
        text = "AI"
        font_size = int(circle_radius * 2.5)  # Start large
        font = load_font(font_size)
        
        # Shrink until text height ~75% of circle diameter (1.5 * radius)
        # AND text width fits inside circle too
        while font_size > 6:
            bbox = draw.textbbox((0, 0), text, font=font)
            text_height = bbox[3] - bbox[1]
            text_width = bbox[2] - bbox[0]
            
            # Check both height AND width fit inside circle
            if text_height <= circle_radius * 1.5 and text_width <= circle_radius * 1.6:
                break
            font_size -= 1
            font = load_font(font_size)
        
        bbox = draw.textbbox((0, 0), text, font=font)
        
        # Calculate position to center text inside the circle
        text_x = center_x - (bbox[2] + bbox[0]) // 2
        text_y = center_y - (bbox[3] + bbox[1]) // 2
        
        # Draw red "AI" text
        draw.text((text_x, text_y), text, fill=text_color, font=font)
        
        images.append(img)
    
    # Save all sizes to one ICO file
    images[0].save(
        output_ico,
        format='ICO',
        sizes=[(img.width, img.height) for img in images],
        append_images=images[1:]
    )
    
    print(f"Icon successfully created: {output_ico}")
    print(f"Sizes: {[f'{s[0]}x{s[1]}' for s in sizes]}")


if __name__ == "__main__":
    # Create icon in current directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    icon_path = os.path.join(script_dir, "app_ai.ico")
    
    create_ai_icon(icon_path)
    
    print("\nIcon generation completed!")
    print(f"ICO file: {icon_path}")
