from flask import Blueprint, render_template, request, jsonify
from deep_translator import GoogleTranslator
from langdetect import detect
import numpy as np
import cohere

chat_blueprint = Blueprint('chat', __name__, template_folder='templates', static_folder='static')
co = cohere.Client('FWvoONoLAQPOsnJcoH2vJl1xbDIiVE0YzlCf8DkB')

@chat_blueprint.route('/')
def chat_page():
    subject = np.random.choice(['/gebra', '/geometry', '/pycode'])
    return render_template('chat.html', title='Chat', chat_css='chat', subject=subject)

@chat_blueprint.route('/response', methods=['POST'])
def chat():
    user_message = request.form['message']

    
    detected_language = detect(user_message)
    
    if detected_language == 'ar':
        
        user_message = GoogleTranslator(source='ar', target='en').translate(user_message)
    
    
    response = co.generate(
        model='command-xlarge',  
        prompt=user_message,
        max_tokens=500
    )
    
    
    bot_message = response.generations[0].text.strip()

    if detected_language == 'ar':
        
        bot_message = GoogleTranslator(source='en', target='ar').translate(bot_message)

    bot_message = bot_message.replace('.', '.<br>').replace(':', ':<br>').replace('?', '?<br>').replace('!', '!<br>') 
    
    return jsonify({'message': bot_message})

if __name__ == '__main__':
    chat_blueprint.run(debug=True)