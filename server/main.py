from datetime import timedelta
import json
import secrets
from flask import Flask, jsonify, make_response, request
import requests
from accesslink import get_latest_exersises, getFIT
from utilities import *
from secret import secret
from flask_cors import CORS
from flask_jwt_extended import JWTManager, create_access_token, jwt_required


# Entrypoint
app = Flask(__name__, static_folder='../build', static_url_path='/')
app.config['JWT_SECRET_KEY'] = secret('SECRET_KEY')
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=1)
jwt = JWTManager(app)

CORS(app, origins=['https://syke-407909.ew.r.appspot.com', 'http://localhost:3000'])

@app.route('/verify', methods=['POST'])
def verify_recaptcha():
    try:
        data = request.get_json()
        captcha_value = data.get('captchaValue')

        # Replace 'YOUR_RECAPTCHA_SECRET_KEY' with your actual reCAPTCHA secret key
        secret_key = secret('RECAPTCHA_PRIVATE_KEY')
        verification_url = f'https://www.google.com/recaptcha/api/siteverify?secret={secret_key}&response={captcha_value}'

        response = requests.post(verification_url)
        result = response.json()

        # Generate a random string of 20 characters
        random_identity = secrets.token_hex(10)

        if result.get('success'):
            access_token = create_access_token(identity=random_identity)
            return jsonify(access_token=access_token), 200
        else:
            return jsonify(message='Invalid reCAPTCHA'), 401
    except Exception as e:
        return jsonify(message=f'Error: {str(e)}'), 401


@app.route("/data", methods=['GET'])
@jwt_required()
def data():
    id=None
    if id is None:
        exe = get_latest_exersises()
        last = None
        i=len(exe)-1
        while i > -1:
            if exe[i]['has_route']:
                last = exe[i]
                break
            i -= 1
        if last:
            id = last['id']
            
    try:
        fit = getFIT(id)
        fit['timestamps'] = removeGpx(fit['timestamps'], 500)
        data = json.dumps(fit)
        response = make_response(data, 200)
        response.headers['Content-Type'] = 'application/json'
    except Exception as e:
        error_message = f"Error: {str(e)}"
        response = make_response(error_message, 500)
        response.headers['Content-Type'] = 'text/plain'
    return response

if __name__ == '__main__':
    app.run(debug=True)