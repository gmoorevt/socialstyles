import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np
from matplotlib.font_manager import FontProperties
import os

def create_social_styles_grid():
    """
    Creates a professional Social Styles grid image with proper quadrants,
    labels, and styling consistent with the application.
    """
    # Create figure and axis
    fig, ax = plt.subplots(figsize=(10, 10))
    
    # Set background color to white
    fig.patch.set_facecolor('white')
    ax.set_facecolor('white')
    
    # Remove axis ticks and spines
    ax.set_xticks([])
    ax.set_yticks([])
    for spine in ax.spines.values():
        spine.set_visible(True)
        spine.set_color('#333333')
        spine.set_linewidth(1.5)
    
    # Set limits
    ax.set_xlim(-1.1, 1.1)
    ax.set_ylim(-1.1, 1.1)
    
    # Draw the quadrants
    quadrant_colors = {
        'amiable': '#f0f8ff',    # Light blue
        'expressive': '#fff0f5',  # Light pink
        'analytical': '#f5fffa',  # Light mint
        'driver': '#fffaf0'       # Light orange
    }
    
    # Create quadrants
    rect_amiable = patches.Rectangle((-1, 0), 1, 1, 
                                    facecolor=quadrant_colors['amiable'], 
                                    edgecolor='#333333', 
                                    linewidth=1.5,
                                    alpha=0.5)
    
    rect_expressive = patches.Rectangle((0, 0), 1, 1, 
                                       facecolor=quadrant_colors['expressive'], 
                                       edgecolor='#333333', 
                                       linewidth=1.5,
                                       alpha=0.5)
    
    rect_analytical = patches.Rectangle((-1, -1), 1, 1, 
                                       facecolor=quadrant_colors['analytical'], 
                                       edgecolor='#333333', 
                                       linewidth=1.5,
                                       alpha=0.5)
    
    rect_driver = patches.Rectangle((0, -1), 1, 1, 
                                   facecolor=quadrant_colors['driver'], 
                                   edgecolor='#333333', 
                                   linewidth=1.5,
                                   alpha=0.5)
    
    # Add quadrants to plot
    ax.add_patch(rect_amiable)
    ax.add_patch(rect_expressive)
    ax.add_patch(rect_analytical)
    ax.add_patch(rect_driver)
    
    # Add axes lines
    ax.axhline(y=0, color='#333333', linestyle='-', linewidth=1.5)
    ax.axvline(x=0, color='#333333', linestyle='-', linewidth=1.5)
    
    # Add title
    plt.title('Social Styles Framework', fontsize=24, fontweight='bold', pad=20)
    
    # Define fonts
    title_font = FontProperties(family='sans-serif', weight='bold', size=16)
    subtitle_font = FontProperties(family='sans-serif', style='italic', size=12)
    axis_font = FontProperties(family='sans-serif', weight='bold', size=14)
    
    # Add quadrant labels
    ax.text(-0.5, 0.5, 'AMIABLE', fontproperties=title_font, ha='center', va='center')
    ax.text(-0.5, 0.35, 'Asks', fontproperties=subtitle_font, ha='center', va='center')
    ax.text(-0.5, 0.25, 'Emotes', fontproperties=subtitle_font, ha='center', va='center')
    
    ax.text(0.5, 0.5, 'EXPRESSIVE', fontproperties=title_font, ha='center', va='center')
    ax.text(0.5, 0.35, 'Tells', fontproperties=subtitle_font, ha='center', va='center')
    ax.text(0.5, 0.25, 'Emotes', fontproperties=subtitle_font, ha='center', va='center')
    
    ax.text(-0.5, -0.5, 'ANALYTICAL', fontproperties=title_font, ha='center', va='center')
    ax.text(-0.5, -0.35, 'Asks', fontproperties=subtitle_font, ha='center', va='center')
    ax.text(-0.5, -0.25, 'Controls', fontproperties=subtitle_font, ha='center', va='center')
    
    ax.text(0.5, -0.5, 'DRIVER', fontproperties=title_font, ha='center', va='center')
    ax.text(0.5, -0.35, 'Tells', fontproperties=subtitle_font, ha='center', va='center')
    ax.text(0.5, -0.25, 'Controls', fontproperties=subtitle_font, ha='center', va='center')
    
    # Add axis labels
    ax.text(0, 1.05, 'High Responsiveness', fontproperties=axis_font, ha='center', va='center')
    ax.text(0, -1.05, 'Low Responsiveness', fontproperties=axis_font, ha='center', va='center')
    ax.text(-1.05, 0, 'Low Assertiveness', fontproperties=axis_font, ha='center', va='center', rotation=90)
    ax.text(1.05, 0, 'High Assertiveness', fontproperties=axis_font, ha='center', va='center', rotation=270)
    
    # Ensure the static/images directory exists
    os.makedirs('static/images', exist_ok=True)
    
    # Save the figure with high DPI for quality
    plt.savefig('static/images/social-styles-grid.png', dpi=300, bbox_inches='tight', transparent=False)
    plt.close()
    
    print("Social Styles grid image created successfully at static/images/social-styles-grid.png")

if __name__ == "__main__":
    create_social_styles_grid() 