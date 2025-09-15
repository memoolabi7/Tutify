import numpy as np
from flask import Blueprint, render_template

account_blueprint = Blueprint('account', __name__, template_folder='templates', static_folder='static')
CHAT_FILE = "data/chat_history.json"

@account_blueprint.route('/')
def account_page():
    subject = np.random.choice(['/gebra', '/geometry', '/pycode'])
    return render_template('account.html', title='Account', account_css='account', subject=subject)