import numpy as np
from flask import Blueprint, render_template

about_blueprint = Blueprint('about', __name__, template_folder='templates', static_folder='static')

@about_blueprint.route('/')
def about_page():
    subject = np.random.choice(['/gebra', '/geometry', '/pycode'])
    return render_template('about.html', title='About Us', about_css='about', subject=subject)