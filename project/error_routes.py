from flask import render_template
from flask_wtf.csrf import CSRFError

from project import application


# Page not found error
@application.errorhandler(404)
def page_not_found(error):
    return render_template('error_404.html'), 404


# Page not found error
@application.errorhandler(CSRFError)
def handle_bad_request(error):
    return render_template('error_400.html'), 400


# Server error
@application.errorhandler(500)
def page_not_found(error):
    return render_template('error_500.html'), 500
