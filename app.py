from flask import Flask, request, jsonify
from flask_cors import CORS
from function.login import authenticate
from function.nesbat_ash8al import * 
import pdfkit

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

# Register the NESBA Blueprint
app.register_blueprint(nesba_blueprint)
# Add this near the top after other imports

# Configure PDFKit - adjust path as needed
PDFKIT_CONFIG = pdfkit.configuration(wkhtmltopdf=r'C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe')
app.config['PDFKIT_CONFIG'] = PDFKIT_CONFIG
@app.route('/login', methods=['POST'])
def login():
    
    """
    Login endpoint: 
    Expects JSON: {"username": "some_user", "password": "some_pass"}
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Request body must be JSON"}), 400

        username = data.get('username')
        password = data.get('password')

        if not username or not password:
            return jsonify({"error": "Missing username or password"}), 400

        # Call your separate auth function from login.py
        success, result = authenticate(username, password)

        if success:
            # 'result' is a dictionary with "user_name" and "group_code"
            return jsonify({
                "message": "Login successful",
                "user_name": result["user_name"],
                "group_code": result["group_code"]
            }), 200
        else:
            # 'result' is an error message string
            return jsonify({"error": result}), 401

    except Exception as e:
        # Catch any unexpected exceptions
        return jsonify({"error": str(e)}), 500
@app.route("/nesba", methods=["GET"])
def nesba_endpoint():
    try:
        # Call the get_data function from nesba_bary
        response = get_data()
        return response  # Assuming get_data already returns a JSON response
    except Exception as e:
        # Catch any unexpected exceptions
        return jsonify({"error": str(e)}), 500
if __name__ == '__main__':
    # Run Flask on port=9999, accessible on all interfaces
    app.run(debug=True, port=2041, host='0.0.0.0')
