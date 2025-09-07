from flask import Blueprint, render_template

pycode_blueprint = Blueprint('pycode', __name__, template_folder='templates', static_folder='static')

@pycode_blueprint.route('/')
def pycode_page():
    return render_template('pycode.html')
