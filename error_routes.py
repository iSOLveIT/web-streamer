from flask import render_template

from project import application


# Page not found error
@application.errorhandler(404)
def page_not_found(error):
    return render_template('error_404.html'), 404


# Server error
@application.errorhandler(500)
def page_not_found(error):
    return render_template('error_500.html'), 500
