import io
import base64
import matplotlib.pyplot as plt
import numpy as np
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from datetime import datetime

def generate_social_style_chart(assertiveness_score, responsiveness_score):
    """Generate a chart showing the user's position in the Social Styles grid.
    
    Args:
        assertiveness_score (float): The user's assertiveness score (1-5)
        responsiveness_score (float): The user's responsiveness score (1-5)
        
    Returns:
        str: Base64-encoded image of the chart
    """
    # Create figure and axis
    fig, ax = plt.figure(figsize=(8, 8)), plt.subplot(111)
    
    # Set up the plot
    ax.set_xlim(1, 5)
    ax.set_ylim(1, 5)
    ax.set_xlabel('Assertiveness', fontsize=14)
    ax.set_ylabel('Responsiveness', fontsize=14)
    ax.set_title('Social Styles Assessment Results', fontsize=16)
    
    # Add grid lines
    ax.grid(True, linestyle='--', alpha=0.7)
    
    # Add quadrant lines
    ax.axhline(y=3, color='black', linestyle='-', alpha=0.5)
    ax.axvline(x=3, color='black', linestyle='-', alpha=0.5)
    
    # Add quadrant labels
    ax.text(2, 2, 'ANALYTICAL', ha='center', va='center', fontsize=12)
    ax.text(4, 2, 'DRIVER', ha='center', va='center', fontsize=12)
    ax.text(2, 4, 'AMIABLE', ha='center', va='center', fontsize=12)
    ax.text(4, 4, 'EXPRESSIVE', ha='center', va='center', fontsize=12)
    
    # Plot the user's position
    ax.plot(assertiveness_score, responsiveness_score, 'ro', markersize=10)
    
    # Add a text label with the exact scores
    ax.text(
        assertiveness_score, 
        responsiveness_score + 0.2, 
        f'({assertiveness_score:.2f}, {responsiveness_score:.2f})', 
        ha='center', 
        va='bottom', 
        fontsize=10
    )
    
    # Save the plot to a bytes buffer
    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=100, bbox_inches='tight')
    plt.close(fig)
    buf.seek(0)
    
    # Convert to base64 for embedding in HTML
    img_str = base64.b64encode(buf.getvalue()).decode('utf-8')
    
    return f'data:image/png;base64,{img_str}'

def get_social_style_description(social_style):
    """Get a description of the social style.
    
    Args:
        social_style (str): The social style (DRIVER, EXPRESSIVE, AMIABLE, ANALYTICAL)
        
    Returns:
        dict: A dictionary with description, strengths, challenges, and tips
    """
    descriptions = {
        'DRIVER': {
            'description': 'Drivers are characterized by high assertiveness and low responsiveness. They are direct, decisive, and results-oriented.',
            'strengths': [
                'Strong decision-making skills',
                'Task-oriented and efficient',
                'Direct and straightforward communication',
                'Goal-focused and determined',
                'Takes initiative and leads by example'
            ],
            'challenges': [
                'May appear impatient or controlling',
                'Can be perceived as insensitive to others\' feelings',
                'May struggle with building personal relationships',
                'Can overlook important details in pursuit of results',
                'May not listen well to others\' input'
            ],
            'tips': [
                'Practice active listening skills',
                'Take time to build relationships with colleagues',
                'Be mindful of how your directness affects others',
                'Acknowledge and appreciate others\' contributions',
                'Consider the human element in decision-making'
            ]
        },
        'EXPRESSIVE': {
            'description': 'Expressives are characterized by high assertiveness and high responsiveness. They are enthusiastic, creative, and people-oriented.',
            'strengths': [
                'Naturally charismatic and engaging',
                'Creative and innovative thinking',
                'Builds relationships easily',
                'Persuasive and inspiring communicator',
                'Energetic and enthusiastic approach'
            ],
            'challenges': [
                'May struggle with follow-through on tasks',
                'Can be perceived as disorganized',
                'May dominate conversations',
                'Can make decisions based on emotions rather than facts',
                'May lose interest in projects over time'
            ],
            'tips': [
                'Develop systems to track details and follow through',
                'Practice listening without interrupting',
                'Balance enthusiasm with practical considerations',
                'Set clear priorities and stick to them',
                'Be mindful of others who need time to process information'
            ]
        },
        'AMIABLE': {
            'description': 'Amiables are characterized by low assertiveness and high responsiveness. They are supportive, patient, and relationship-oriented.',
            'strengths': [
                'Strong team player and collaborator',
                'Excellent listening skills',
                'Patient and supportive of others',
                'Creates harmony in groups',
                'Builds deep, trusting relationships'
            ],
            'challenges': [
                'May avoid necessary conflict',
                'Can struggle with making quick decisions',
                'May have difficulty saying "no"',
                'Can be overly concerned with others\' opinions',
                'May not assert their own needs effectively'
            ],
            'tips': [
                'Practice asserting your opinions and needs',
                'Develop comfort with healthy conflict',
                'Set boundaries to avoid overcommitment',
                'Trust your own judgment more often',
                'Balance relationship concerns with task completion'
            ]
        },
        'ANALYTICAL': {
            'description': 'Analyticals are characterized by low assertiveness and low responsiveness. They are logical, thorough, and detail-oriented.',
            'strengths': [
                'Thorough and detail-oriented approach',
                'Strong critical thinking skills',
                'Logical and methodical problem-solving',
                'High-quality work with few errors',
                'Thoughtful and careful decision-making'
            ],
            'challenges': [
                'May be perceived as overly critical or perfectionistic',
                'Can struggle with making quick decisions',
                'May have difficulty expressing emotions',
                'Can get caught in "analysis paralysis"',
                'May not connect easily with others'
            ],
            'tips': [
                'Practice making decisions with limited information',
                'Share your thought process with others',
                'Make an effort to connect personally with colleagues',
                'Be mindful of perfectionist tendencies',
                'Consider the big picture alongside the details'
            ]
        }
    }
    
    return descriptions.get(social_style, {
        'description': 'No description available.',
        'strengths': [],
        'challenges': [],
        'tips': []
    })

def generate_pdf_report(result, chart_img, user):
    """Generate a PDF report of the assessment results.
    
    Args:
        result (AssessmentResult): The assessment result
        chart_img (str): Base64-encoded image of the social styles chart
        user (User): The user who took the assessment
        
    Returns:
        io.BytesIO: A buffer containing the PDF
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    
    # Create custom styles
    title_style = ParagraphStyle(
        'Title',
        parent=styles['Heading1'],
        fontSize=18,
        alignment=1,  # Center alignment
        spaceAfter=12
    )
    
    heading2_style = ParagraphStyle(
        'Heading2',
        parent=styles['Heading2'],
        fontSize=14,
        spaceBefore=12,
        spaceAfter=6
    )
    
    heading3_style = ParagraphStyle(
        'Heading3',
        parent=styles['Heading3'],
        fontSize=12,
        spaceBefore=8,
        spaceAfter=4
    )
    
    normal_style = styles['Normal']
    
    # Get social style description
    style_info = get_social_style_description(result.social_style)
    
    # Create the content
    content = []
    
    # Title
    content.append(Paragraph("Social Styles Assessment Report", title_style))
    content.append(Spacer(1, 0.25*inch))
    
    # User info and date
    content.append(Paragraph(f"Name: {user.name}", normal_style))
    content.append(Paragraph(f"Email: {user.email}", normal_style))
    content.append(Paragraph(f"Date: {result.created_at.strftime('%B %d, %Y')}", normal_style))
    content.append(Spacer(1, 0.25*inch))
    
    # Results summary
    content.append(Paragraph("Assessment Results", heading2_style))
    content.append(Paragraph(f"Your Social Style: <b>{result.social_style}</b>", normal_style))
    content.append(Paragraph(f"Assertiveness Score: {result.assertiveness_score:.2f}/4.0", normal_style))
    content.append(Paragraph(f"Responsiveness Score: {result.responsiveness_score:.2f}/4.0", normal_style))
    content.append(Spacer(1, 0.25*inch))
    
    # Convert chart image from base64 to Image
    if chart_img:
        img_data = chart_img.split(',')[1]
        img_bytes = base64.b64decode(img_data)
        img_buffer = io.BytesIO(img_bytes)
        img = Image(img_buffer, width=6*inch, height=6*inch)
        content.append(img)
    
    content.append(Spacer(1, 0.25*inch))
    
    # Social style description
    content.append(Paragraph(f"Understanding Your {result.social_style} Style", heading2_style))
    content.append(Paragraph(style_info['description'], normal_style))
    content.append(Spacer(1, 0.15*inch))
    
    # Strengths
    content.append(Paragraph("Strengths:", heading2_style))
    for strength in style_info['strengths']:
        content.append(Paragraph(f"• {strength}", normal_style))
    content.append(Spacer(1, 0.15*inch))
    
    # Challenges
    content.append(Paragraph("Challenges:", heading2_style))
    for challenge in style_info['challenges']:
        content.append(Paragraph(f"• {challenge}", normal_style))
    content.append(Spacer(1, 0.15*inch))
    
    # Tips
    content.append(Paragraph("Development Tips:", heading2_style))
    for tip in style_info['tips']:
        content.append(Paragraph(f"• {tip}", normal_style))
    content.append(Spacer(1, 0.25*inch))
    
    # Add style interactions section
    content.append(Paragraph("How Your Style Interacts with Others", heading2_style))
    content.append(Paragraph(f"Understanding how your {result.social_style.lower()} style typically interacts with other styles can help you build more effective relationships:", normal_style))
    content.append(Spacer(1, 0.15*inch))
    
    # Add interaction details based on the user's style
    if result.social_style == 'DRIVER':
        # Driver + Analytical
        content.append(Paragraph("Driver + Analytical", heading3_style))
        content.append(Paragraph("<b>Strengths:</b> Both are task-focused and value efficiency", normal_style))
        content.append(Paragraph("<b>Challenges:</b> You may become impatient with their detailed analysis", normal_style))
        content.append(Paragraph("<b>Tip:</b> Allow time for Analyticals to process information and consider all angles", normal_style))
        content.append(Spacer(1, 0.1*inch))
        
        # Driver + Expressive
        content.append(Paragraph("Driver + Expressive", heading3_style))
        content.append(Paragraph("<b>Strengths:</b> Both are assertive and quick to make decisions", normal_style))
        content.append(Paragraph("<b>Challenges:</b> You focus on tasks while they prioritize relationships", normal_style))
        content.append(Paragraph("<b>Tip:</b> Acknowledge their creative ideas and enthusiasm before moving to action", normal_style))
        content.append(Spacer(1, 0.1*inch))
        
        # Driver + Amiable
        content.append(Paragraph("Driver + Amiable", heading3_style))
        content.append(Paragraph("<b>Strengths:</b> Complementary skills—you provide direction, they provide support", normal_style))
        content.append(Paragraph("<b>Challenges:</b> You may appear too forceful; they may seem too slow to decide", normal_style))
        content.append(Paragraph("<b>Tip:</b> Soften your approach and show appreciation for their supportive nature", normal_style))
        
    elif result.social_style == 'ANALYTICAL':
        # Analytical + Driver
        content.append(Paragraph("Analytical + Driver", heading3_style))
        content.append(Paragraph("<b>Strengths:</b> You provide thorough information they can use to make decisions", normal_style))
        content.append(Paragraph("<b>Challenges:</b> You may provide too much detail for their preference", normal_style))
        content.append(Paragraph("<b>Tip:</b> Lead with conclusions and recommendations, then provide details as needed", normal_style))
        content.append(Spacer(1, 0.1*inch))
        
        # Analytical + Expressive
        content.append(Paragraph("Analytical + Expressive", heading3_style))
        content.append(Paragraph("<b>Strengths:</b> You bring precision while they bring creativity", normal_style))
        content.append(Paragraph("<b>Challenges:</b> You prefer facts while they prefer concepts", normal_style))
        content.append(Paragraph("<b>Tip:</b> Acknowledge their enthusiasm while gently asking for supporting data", normal_style))
        content.append(Spacer(1, 0.1*inch))
        
        # Analytical + Amiable
        content.append(Paragraph("Analytical + Amiable", heading3_style))
        content.append(Paragraph("<b>Strengths:</b> Both are thoughtful and careful in approach", normal_style))
        content.append(Paragraph("<b>Challenges:</b> Together you may avoid making quick decisions", normal_style))
        content.append(Paragraph("<b>Tip:</b> Set deadlines for decisions and focus on practical applications", normal_style))
        
    elif result.social_style == 'EXPRESSIVE':
        # Expressive + Driver
        content.append(Paragraph("Expressive + Driver", heading3_style))
        content.append(Paragraph("<b>Strengths:</b> You generate ideas that Drivers can implement", normal_style))
        content.append(Paragraph("<b>Challenges:</b> You may seem unfocused to them", normal_style))
        content.append(Paragraph("<b>Tip:</b> Be concise and results-oriented when working with Drivers", normal_style))
        content.append(Spacer(1, 0.1*inch))
        
        # Expressive + Analytical
        content.append(Paragraph("Expressive + Analytical", heading3_style))
        content.append(Paragraph("<b>Strengths:</b> Your creativity complements their precision", normal_style))
        content.append(Paragraph("<b>Challenges:</b> You may find them too rigid; they may find you disorganized", normal_style))
        content.append(Paragraph("<b>Tip:</b> Provide data points to support your creative ideas", normal_style))
        content.append(Spacer(1, 0.1*inch))
        
        # Expressive + Amiable
        content.append(Paragraph("Expressive + Amiable", heading3_style))
        content.append(Paragraph("<b>Strengths:</b> Both are people-oriented and value relationships", normal_style))
        content.append(Paragraph("<b>Challenges:</b> Your energy may overwhelm quieter Amiables", normal_style))
        content.append(Paragraph("<b>Tip:</b> Create space for Amiables to contribute their thoughts", normal_style))
        
    elif result.social_style == 'AMIABLE':
        # Amiable + Driver
        content.append(Paragraph("Amiable + Driver", heading3_style))
        content.append(Paragraph("<b>Strengths:</b> You support implementation of their decisions", normal_style))
        content.append(Paragraph("<b>Challenges:</b> You may feel rushed; they may feel slowed down", normal_style))
        content.append(Paragraph("<b>Tip:</b> Establish clear timelines and expectations upfront", normal_style))
        content.append(Spacer(1, 0.1*inch))
        
        # Amiable + Analytical
        content.append(Paragraph("Amiable + Analytical", heading3_style))
        content.append(Paragraph("<b>Strengths:</b> Both are careful and methodical", normal_style))
        content.append(Paragraph("<b>Challenges:</b> Together you may get stuck in analysis", normal_style))
        content.append(Paragraph("<b>Tip:</b> Focus on practical applications and set decision deadlines", normal_style))
        content.append(Spacer(1, 0.1*inch))
        
        # Amiable + Expressive
        content.append(Paragraph("Amiable + Expressive", heading3_style))
        content.append(Paragraph("<b>Strengths:</b> Both value personal connections and harmony", normal_style))
        content.append(Paragraph("<b>Challenges:</b> You may be overwhelmed by their energy", normal_style))
        content.append(Paragraph("<b>Tip:</b> Share your perspectives confidently; they'll appreciate your input", normal_style))
    
    content.append(Spacer(1, 0.2*inch))
    
    # Add adaptation strategies
    content.append(Paragraph("Adaptation Strategies", heading3_style))
    content.append(Paragraph("1. Recognize others' styles through their communication patterns", normal_style))
    content.append(Paragraph("2. Temporarily adjust your approach to better connect with different styles", normal_style))
    content.append(Paragraph("3. Find common ground rather than expecting others to fully adapt to you", normal_style))
    content.append(Paragraph("4. Remember that diverse styles bring complementary strengths to teams", normal_style))
    
    # Build the PDF
    doc.build(content)
    
    return buffer 