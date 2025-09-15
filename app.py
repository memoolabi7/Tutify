from flask import Flask, render_template
import numpy as np
from gebra import gebra_blueprint
from geometry import geometry_blueprint
from pycode import pycode_blueprint
from chat import chat_blueprint
from account import account_blueprint
from about import about_blueprint

app = Flask(__name__, template_folder='templates', static_folder='static')
app.secret_key = "gebra"

app.register_blueprint(gebra_blueprint, url_prefix='/gebra')
app.register_blueprint(geometry_blueprint, url_prefix='/geometry')
app.register_blueprint(pycode_blueprint, url_prefix='/pycode')
app.register_blueprint(chat_blueprint, url_prefix='/chat')
app.register_blueprint(account_blueprint, url_prefix='/account')
app.register_blueprint(about_blueprint, url_prefix='/about')

@app.route('/')
def index():
    return render_template('index.html', title='Welcome to Tutify!')

@app.route('/main')
def main():
    subject = np.random.choice(['/gebra', '/geometry', '/pycode'])
    return render_template('main.html', title='Tutify', subject=subject)

if __name__ == '__main__':
    app.run()