from flask import Flask, jsonify, request, render_template
import requests
from requests.exceptions import RequestException

app = Flask(__name__)

LOGIC_URL = "https://sanqiqi7.pythonanywhere.com/logic/holidays"

def forward_to_logic(params):
    """
    Unified Request Forwarding: Transmits client requests transparently to Logic Service while handling potential connection anomalies.
    """
    try:
        response = requests.get(LOGIC_URL, params=params, timeout=10)
        return jsonify(response.json()) 
    except RequestException as e:
        return jsonify({"error": f"Logic Service unavailable: {e}"}), 503
@app.route('/holidays/<country>/<year>', methods=['GET'])
def get_holidays_year(country, year):
    return forward_to_logic({"country": country, "year": year})

@app.route('/holidays/<country>/<year>/<month>', methods=['GET'])
def get_holidays_month(country, year, month):
    return forward_to_logic({"country": country, "year": year, "month": month})

@app.route('/holidays/<country>/<year>/name/<name>', methods=['GET'])
def get_holidays_name(country, year, name):
    return forward_to_logic({"country": country, "year": year, "name": name})

@app.route('/', methods=['GET'])
def query_ui():
    """
    Provide user interface (HTML)
    """
    # Based on Logic Service support, provide CN and IE
    supported_countries = ['CN', 'IE'] 
    
    # Assume query range is this year to the next two years
    current_year = 2025 # Assume current year is 2025
    supported_years = [str(current_year + i) for i in range(3)] 
    
    # Render HTML template and pass data to the template
    return render_template(
        'query_form.html',
        countries=supported_countries,
        years=supported_years
    )

@app.route("/gateway/test", methods=["GET"])
def test():
    return jsonify({"message": "r Group Gateway Service is running"}), 200

if __name__ == '__main__':
    app.run(debug=True, port=5002)

