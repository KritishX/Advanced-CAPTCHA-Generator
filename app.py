# Import all required libraries and modules
from flask import Flask, render_template, request, session, redirect, url_for, send_file, jsonify
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance  # For image manipulation
import random  # For generating random CAPTCHA text
import string  # For string operations
import io  # For handling byte streams
import os  # For file system operations
import hashlib  # For secure hashing
import time  # For timing operations
from datetime import datetime, timedelta  # For time calculations
import logging  # For logging events
from functools import wraps  # For decorators
import math  # For mathematical operations

# Configure logging to both file and console
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('captcha.log'),  # Log to file
        logging.StreamHandler()  # Log to console
    ]
)

# Initialize Flask application
app = Flask(__name__)
# Set secret key for session management (should be changed in production)
app.secret_key = os.environ.get('SECRET_KEY', 'your-super-secret-key-change-this-in-production')

# Configuration class for CAPTCHA settings
class Config:
    CAPTCHA_LENGTH = 6  # Length of CAPTCHA text
    CAPTCHA_TIMEOUT = 300  # 5 minutes timeout for CAPTCHA validity
    MAX_ATTEMPTS = 3  # Maximum allowed attempts per CAPTCHA
    # List of font paths to use for CAPTCHA text
    FONT_PATHS = [
        os.path.join('static', 'fonts', 'DejaVuSans-Bold.ttf'),
        os.path.join('static', 'fonts', 'Arial-Bold.ttf'),
        os.path.join('static', 'fonts', 'Helvetica-Bold.ttf')
    ]
    IMAGE_WIDTH = 300  # Width of CAPTCHA image
    IMAGE_HEIGHT = 120  # Height of CAPTCHA image
    NOISE_LEVEL = 'medium'  # Noise level for CAPTCHA image (low, medium, high)

# Rate limiting decorator to prevent abuse
def rate_limit(max_requests=10, window=60):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Initialize rate limit tracking in session if not exists
            if 'rate_limit' not in session:
                session['rate_limit'] = {'count': 0, 'timestamp': time.time()}
            
            current_time = time.time()
            # Reset count if time window has passed
            if current_time - session['rate_limit']['timestamp'] > window:
                session['rate_limit'] = {'count': 0, 'timestamp': current_time}
            
            # Check if rate limit exceeded
            if session['rate_limit']['count'] >= max_requests:
                return jsonify({'error': 'Rate limit exceeded. Please try again later.'}), 429
            
            # Increment request count
            session['rate_limit']['count'] += 1
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# CAPTCHA generator class that handles all CAPTCHA creation logic
class CaptchaGenerator:
    def __init__(self, config):
        self.config = config  # Store configuration
        self.logger = logging.getLogger(__name__)  # Initialize logger
        
    def generate_captcha_text(self, length=None):
        """Generate random CAPTCHA text with improved character selection"""
        if length is None:
            length = self.config.CAPTCHA_LENGTH
        
        # Use characters that are easy to distinguish (excludes 0, O, I, l, 1)
        characters = 'ABCDEFGHIJKLMNPQRSTUVWXYZ23456789'
        return ''.join(random.choice(characters) for _ in range(length))
    
    def get_random_color(self, color_type='dark'):
        """Generate random colors based on type (dark, light, medium)"""
        if color_type == 'dark':
            return (random.randint(0, 100), random.randint(0, 100), random.randint(0, 100))
        elif color_type == 'light':
            return (random.randint(150, 255), random.randint(150, 255), random.randint(150, 255))
        else:  # medium
            return (random.randint(50, 150), random.randint(50, 150), random.randint(50, 150))
    
    def load_font(self, size=48):
        """Load font with fallback options"""
        # Try each font path in order
        for font_path in self.config.FONT_PATHS:
            try:
                if os.path.exists(font_path):
                    return ImageFont.truetype(font_path, size)
            except IOError:
                continue
        
        # Fallback to default font if no custom fonts found
        try:
            return ImageFont.load_default()
        except:
            return ImageFont.load_default()
    
    def add_background_gradient(self, image, draw):
        """Add gradient background to CAPTCHA image"""
        width, height = image.size
        color1 = self.get_random_color('light')
        color2 = self.get_random_color('light')
        
        # Create vertical gradient
        for y in range(height):
            r = int(color1[0] + (color2[0] - color1[0]) * y / height)
            g = int(color1[1] + (color2[1] - color1[1]) * y / height)
            b = int(color1[2] + (color2[2] - color1[2]) * y / height)
            draw.line([(0, y), (width, y)], fill=(r, g, b))
    
    def add_geometric_noise(self, image, draw):
        """Add geometric shapes as noise to make CAPTCHA harder to read by bots"""
        width, height = image.size
        
        # Add random circles
        for _ in range(random.randint(3, 8)):
            x = random.randint(0, width)
            y = random.randint(0, height)
            radius = random.randint(5, 25)
            color = self.get_random_color('medium')
            draw.ellipse([x-radius, y-radius, x+radius, y+radius], 
                        outline=color, width=2)
        
        # Add random rectangles
        for _ in range(random.randint(2, 5)):
            x1 = random.randint(0, width//2)
            y1 = random.randint(0, height//2)
            x2 = x1 + random.randint(20, 60)
            y2 = y1 + random.randint(10, 30)
            color = self.get_random_color('medium')
            draw.rectangle([x1, y1, x2, y2], outline=color, width=1)
    
    def add_wave_distortion(self, image):
        """Add wave distortion to make text harder to read by OCR"""
        width, height = image.size
        distorted = Image.new('RGB', (width, height), (255, 255, 255))
        
        # Apply sine wave distortion to each pixel
        for x in range(width):
            for y in range(height):
                offset_x = int(5 * math.sin(y * 0.1))
                offset_y = int(3 * math.sin(x * 0.1))
                
                new_x = min(max(x + offset_x, 0), width - 1)
                new_y = min(max(y + offset_y, 0), height - 1)
                
                try:
                    distorted.putpixel((x, y), image.getpixel((new_x, new_y)))
                except:
                    distorted.putpixel((x, y), (255, 255, 255))
        
        return distorted
    
    def generate_captcha_image(self, text):
        """Generate complete CAPTCHA image with all effects"""
        width, height = self.config.IMAGE_WIDTH, self.config.IMAGE_HEIGHT
        
        # Create base image
        image = Image.new('RGB', (width, height), (255, 255, 255))
        draw = ImageDraw.Draw(image)
        
        # Add gradient background
        self.add_background_gradient(image, draw)
        
        # Load random font size
        font = self.load_font(random.randint(40, 55))
        
        # Calculate text positioning
        char_spacing = width // (len(text) + 1)
        
        # Draw each character with individual effects
        for i, char in enumerate(text):
            # Random position with some constraints
            x = char_spacing * (i + 1) + random.randint(-15, 15)
            y = height // 2 + random.randint(-20, 20)
            
            # Random rotation
            angle = random.randint(-30, 30)
            
            # Create character image with transparency
            char_img = Image.new('RGBA', (80, 80), (255, 255, 255, 0))
            char_draw = ImageDraw.Draw(char_img)
            
            # Add shadow effect
            shadow_color = self.get_random_color('dark')
            char_draw.text((12, 12), char, font=font, fill=shadow_color + (100,))
            
            # Add main character
            char_color = self.get_random_color('dark')
            char_draw.text((10, 10), char, font=font, fill=char_color)
            
            # Rotate character
            rotated_char = char_img.rotate(angle, expand=1)
            
            # Paste onto main image
            image.paste(rotated_char, (x-40, y-40), rotated_char)
        
        # Add noise based on configuration
        if self.config.NOISE_LEVEL == 'low':
            self.add_light_noise(image, draw)
        elif self.config.NOISE_LEVEL == 'medium':
            self.add_medium_noise(image, draw)
        else:  # high
            self.add_heavy_noise(image, draw)
        
        # Add geometric noise
        self.add_geometric_noise(image, draw)
        
        # Apply image filters
        image = image.filter(ImageFilter.SMOOTH_MORE)
        
        # Add wave distortion
        image = self.add_wave_distortion(image)
        
        # Enhance image contrast
        enhancer = ImageEnhance.Contrast(image)
        image = enhancer.enhance(1.2)
        
        # Final smoothing
        image = image.filter(ImageFilter.SMOOTH)
        
        self.logger.info(f"Generated CAPTCHA image for text: {text}")
        return image
    
    def add_light_noise(self, image, draw):
        """Add light noise (random dots)"""
        width, height = image.size
        for _ in range(50):
            x = random.randint(0, width)
            y = random.randint(0, height)
            draw.point((x, y), fill=self.get_random_color('medium'))
    
    def add_medium_noise(self, image, draw):
        """Add medium noise (dots and lines)"""
        width, height = image.size
        
        # Add random dots
        for _ in range(100):
            x = random.randint(0, width)
            y = random.randint(0, height)
            draw.point((x, y), fill=self.get_random_color('medium'))
        
        # Add random lines
        for _ in range(8):
            x1 = random.randint(0, width)
            y1 = random.randint(0, height)
            x2 = random.randint(0, width)
            y2 = random.randint(0, height)
            draw.line([(x1, y1), (x2, y2)], fill=self.get_random_color('medium'), width=1)
    
    def add_heavy_noise(self, image, draw):
        """Add heavy noise (more dots and thicker lines)"""
        width, height = image.size
        
        # Add many random dots
        for _ in range(200):
            x = random.randint(0, width)
            y = random.randint(0, height)
            draw.point((x, y), fill=self.get_random_color('medium'))
        
        # Add multiple thick lines
        for _ in range(15):
            x1 = random.randint(0, width)
            y1 = random.randint(0, height)
            x2 = random.randint(0, width)
            y2 = random.randint(0, height)
            draw.line([(x1, y1), (x2, y2)], fill=self.get_random_color('medium'), width=2)

# Initialize CAPTCHA generator with configuration
captcha_gen = CaptchaGenerator(Config)

def generate_captcha_hash(text, timestamp):
    """Generate secure hash for CAPTCHA validation using SHA-256"""
    return hashlib.sha256(f"{text}:{timestamp}:{app.secret_key}".encode()).hexdigest()

def validate_captcha_session():
    """Validate CAPTCHA session data"""
    if 'captcha_data' not in session:
        return False
    
    captcha_data = session['captcha_data']
    current_time = time.time()
    
    # Check if CAPTCHA has expired
    if current_time - captcha_data['timestamp'] > Config.CAPTCHA_TIMEOUT:
        return False
    
    # Check if maximum attempts reached
    if captcha_data.get('attempts', 0) >= Config.MAX_ATTEMPTS:
        return False
    
    return True

# Flask route handlers

@app.route('/')
def index():
    """Main CAPTCHA page that generates a new CAPTCHA"""
    # Generate new CAPTCHA text
    captcha_text = captcha_gen.generate_captcha_text()
    timestamp = time.time()
    
    # Store CAPTCHA data in session
    session['captcha_data'] = {
        'text': captcha_text,
        'timestamp': timestamp,
        'hash': generate_captcha_hash(captcha_text, timestamp),
        'attempts': 0
    }
    
    # Render the main page with CAPTCHA
    return render_template('index.html', config=Config)

@app.route('/captcha_image')
@rate_limit(max_requests=20, window=60)
def captcha_image():
    """Generate and serve CAPTCHA image with rate limiting"""
    if not validate_captcha_session():
        # Redirect if session is invalid
        return redirect(url_for('index'))
    
    # Get CAPTCHA text from session
    captcha_text = session['captcha_data']['text']
    # Generate image
    image = captcha_gen.generate_captcha_image(captcha_text)
    
    # Save image to in-memory bytes
    img_io = io.BytesIO()
    image.save(img_io, 'PNG', optimize=True)
    img_io.seek(0)
    
    # Send image as response
    return send_file(img_io, mimetype='image/png', as_attachment=False, 
                     download_name='captcha.png')

@app.route('/refresh_captcha')
@rate_limit(max_requests=5, window=60)
def refresh_captcha():
    """Refresh CAPTCHA (AJAX endpoint) with rate limiting"""
    # Generate new CAPTCHA
    captcha_text = captcha_gen.generate_captcha_text()
    timestamp = time.time()
    
    # Update session with new CAPTCHA
    session['captcha_data'] = {
        'text': captcha_text,
        'timestamp': timestamp,
        'hash': generate_captcha_hash(captcha_text, timestamp),
        'attempts': 0
    }
    
    # Return success response
    return jsonify({'status': 'success', 'message': 'CAPTCHA refreshed'})

@app.route('/verify', methods=['POST'])
@rate_limit(max_requests=15, window=60)
def verify():
    """Verify CAPTCHA input with rate limiting"""
    if not validate_captcha_session():
        return render_template('result.html', 
                             success=False, 
                             message='CAPTCHA session expired. Please try again.',
                             error_type='expired')
    
    # Get user input and normalize
    user_input = request.form.get('captcha_input', '').strip().upper()
    captcha_data = session['captcha_data']
    
    # Increment attempt count
    captcha_data['attempts'] = captcha_data.get('attempts', 0) + 1
    session['captcha_data'] = captcha_data
    
    # Validate input against stored CAPTCHA
    if user_input == captcha_data['text']:
        # Clear session on success
        session.pop('captcha_data', None)
        
        app.logger.info(f"CAPTCHA verification successful for text: {captcha_data['text']}")
        return render_template('result.html', 
                             success=True, 
                             message='CAPTCHA verified successfully!')
    else:
        remaining_attempts = Config.MAX_ATTEMPTS - captcha_data['attempts']
        
        if remaining_attempts <= 0:
            app.logger.warning(f"Max attempts reached for CAPTCHA: {captcha_data['text']}")
            return render_template('result.html', 
                                 success=False, 
                                 message='Maximum attempts reached. Please start over.',
                                 error_type='max_attempts')
        
        app.logger.info(f"CAPTCHA verification failed. Attempts remaining: {remaining_attempts}")
        return render_template('result.html', 
                             success=False, 
                             message=f'Incorrect CAPTCHA. {remaining_attempts} attempts remaining.',
                             error_type='incorrect',
                             attempts_remaining=remaining_attempts)

# Error handlers

@app.errorhandler(429)
def rate_limit_exceeded(e):
    """Handle rate limit exceeded errors"""
    return render_template('result.html', 
                         success=False, 
                         message='Too many requests. Please try again later.',
                         error_type='rate_limit'), 429

@app.errorhandler(500)
def internal_error(e):
    """Handle internal server errors"""
    app.logger.error(f"Internal server error: {str(e)}")
    return render_template('result.html', 
                         success=False, 
                         message='An internal error occurred. Please try again.',
                         error_type='server_error'), 500

# Main entry point
if __name__ == '__main__':
    # Create necessary directories
    os.makedirs('static/fonts', exist_ok=True)
    
    # Run the Flask application
    app.run(debug=False, host='0.0.0.0', port=5000)