"""
StayScout - AI-Powered Vacation Rental Price Comparison
Production-ready Flask application for Vercel deployment
"""

import os
from flask import Flask, render_template, jsonify, request
from demo_results import DEMO_RESULTS, get_demo_result

# Initialize Flask app
app = Flask(__name__)

# Configuration
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['ENV'] = os.environ.get('FLASK_ENV', 'production')

# Brand configuration
BRAND_CONFIG = {
    'name': 'StayScout',
    'domain': 'stayscoutapp.com',
    'tagline': 'Find the Best Price for Your Perfect Stay',
    'description': 'AI-powered search to find vacation rentals at the lowest price across all booking platforms'
}


@app.route('/')
def home():
    """Landing page with demo showcase"""
    demo_data = get_demo_result("demo_park_city_condo")
    return render_template('home.html',
                         brand=BRAND_CONFIG,
                         demo_data=demo_data)


@app.route('/demo')
def demo():
    """Interactive demo page"""
    # Default to Park City demo
    demo_key = request.args.get('demo', 'demo_park_city_condo')
    demo_data = get_demo_result(demo_key)

    if not demo_data:
        demo_data = get_demo_result("demo_park_city_condo")

    return render_template('demo.html',
                         brand=BRAND_CONFIG,
                         demo_data=demo_data,
                         available_demos=list(DEMO_RESULTS.keys()))


@app.route('/about')
def about():
    """About StayScout page"""
    return render_template('about.html', brand=BRAND_CONFIG)


@app.route('/api/demo-results')
def api_demo_results():
    """API endpoint for demo results (for future AJAX calls)"""
    demo_key = request.args.get('demo', 'demo_park_city_condo')
    demo_data = get_demo_result(demo_key)

    if not demo_data:
        return jsonify({'error': 'Demo not found'}), 404

    return jsonify(demo_data)


@app.route('/health')
def health():
    """Health check endpoint for monitoring"""
    return jsonify({
        'status': 'healthy',
        'service': 'StayScout Demo',
        'version': '1.0.0'
    })


@app.errorhandler(404)
def not_found(e):
    """Custom 404 page"""
    return render_template('404.html', brand=BRAND_CONFIG), 404


@app.errorhandler(500)
def server_error(e):
    """Custom 500 page"""
    return render_template('500.html', brand=BRAND_CONFIG), 500


# Template filters for better formatting
@app.template_filter('currency')
def currency_filter(value):
    """Format value as USD currency"""
    try:
        return f"${float(value):,.2f}"
    except (ValueError, TypeError):
        return f"${value}"


@app.template_filter('percentage')
def percentage_filter(value):
    """Format value as percentage"""
    try:
        return f"{float(value):.1f}%"
    except (ValueError, TypeError):
        return f"{value}%"


# For local development
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV') == 'development'
    app.run(host='0.0.0.0', port=port, debug=debug)
