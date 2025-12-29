from flask import Flask, request, jsonify
import requests
from datetime import datetime, timedelta, timezone
from requests.exceptions import RequestException
import logging

# Log configuration: Set the log level to INFO to record running information. 
logging.basicConfig(level=logging.INFO)

app = Flask(__name__)

DB_SERVICE_BASE_URL = "https://hua123456.pythonanywhere.com"
NAGER_DATE_API_BASE_URL = "https://date.nager.at/api/v3/PublicHolidays"

CACHE_EXPIRY_HOURS = 1

SUPPORTED_COUNTRIES = ['CN', 'IE']

def process_raw_data(raw_holiday_list, country_code):
    processed_list = []

    for holiday in raw_holiday_list:
        if 'date' in holiday and 'name' in holiday:
            try:
                date = datetime.strptime(holiday['date'], '%Y-%m-%d')
                month = str(date.month).zfill(2)

                processed_list.append({
                    "date": holiday['date'],
                    "countryCode": country_code,
                    "month": month,
                    "name": holiday['name'],
                })
            except ValueError:
                app.logger.warning(f"Skipping invalid date format.")
                continue
    return processed_list

def is_cache_expired(cached_data):
    if not cached_data:
        return True

    try:
        cache_time_str = cached_data[0].get('cache_time')

        if not cache_time_str:
            app.logger.info("No 'cache_time' found in data, considering as expired.")
            return True
        
        cache_time = datetime.strptime(cache_time_str, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)

        expiry_time = cache_time + timedelta(hours=CACHE_EXPIRY_HOURS)

        current_time = datetime.now(timezone.utc)
        # Use Time Expiration Check
        is_expired = current_time > expiry_time

        if is_expired:
            app.logger.info(f"Cache expired. Expiry time: {expiry_time.strftime('%Y-%m-%d %H:%M:%S %Z')}")
        else:
            remaining_time = expiry_time - current_time
            app.logger.info(f"Cache valid. Remaining valid time: {remaining_time}")

        return is_expired

    except ValueError as e:
        app.logger.warning(f"Time format error: {e}, considering cache expired.")
        return True
    except KeyError as e:
        app.logger.warning(f"Missing required key 'cache_time' in cache data, considering cache expired.")
        return True
    except IndexError as e:
        app.logger.warning(f"Cache data is empty or invalid structure: {e}, considering cache expired.")
        return True
    except TypeError as e:
        app.logger.warning(f"Data type error in cache processing: {e}, considering cache expired.")
        return True


def check_cache(db_query_url, country, year):
    try:
        # Add timeout handling for DB service requests
        db_response = requests.get(db_query_url, timeout=10)

        if db_response.status_code == 200:
            cached_data = db_response.json().get('data', [])

            if cached_data and not is_cache_expired(cached_data):
                app.logger.info(f"Cached data is valid for {country} {year}.")
                return cached_data, True
            else:
                app.logger.info(f"Cache for {country} {year} is either empty or expired.")
                return cached_data, False  

        # Add specific handling for 404 cache miss scenarios
        elif db_response.status_code == 404:
            app.logger.info(f"Cache miss for {country} {year}. No data found in DB.")
            return None, False

        else:
            app.logger.warning(f"DB Service error during query: {db_response.status_code}. Attempting external API fetch.")
            return None, False

    except RequestException as e:
        app.logger.warning(f"DB Service connection/timeout error: {e}. Attempting external API fetch.")
        return None, False
    except Exception as e:
        # Logging other unexpected errors
        app.logger.error(f"Cache check failed: {e}")
        return None, False


def get_holidays_data(country, year, month=None, name=None):
    # Add the country and year required for querying the database
    if not country or not year:
        return jsonify({"error": "Missing required parameters: country and year"}), 400

    country_upper = country.upper()

    # Use the SUPPORTED_COUNTRIES constant for country codes
    if country_upper not in SUPPORTED_COUNTRIES:
        return jsonify({"error": f"Unsupported country code: {country}"}), 400
    
    # Add internal routing mappings (CN for china, IE for Ireland) to resolve database endpoint issues
    if country_upper == 'CN':
        route_name = 'china'
    elif country_upper == 'IE':
        route_name = 'ireland'

    db_query_url = f"{DB_SERVICE_BASE_URL}/db/get-{route_name}?year={year}"

    db_save_url = f"{DB_SERVICE_BASE_URL}/db/save-{route_name}"

    external_api_url = f"{NAGER_DATE_API_BASE_URL}/{year}/{country_upper}"

    cached_data = None
    final_data = []  
    data_source = "api"  

    #cache check
    cached_data, is_cache_valid = check_cache(db_query_url, country_upper, year)

    if is_cache_valid:
        final_data = cached_data
        data_source = "cache"
    else:
        try:
            app.logger.info(f"Fetching data from external API: {external_api_url}")
            api_response = requests.get(external_api_url, timeout=30)
            api_response.raise_for_status()  
            raw_data = api_response.json()

            processed_data = process_raw_data(raw_data, country_upper)
            final_data = processed_data 

            if processed_data:
                try:
                    save_response = requests.post(db_save_url, json=processed_data, timeout=10)
                    save_response.raise_for_status()
                    app.logger.info(f"Successfully saved {len(processed_data)} records to DB.")
                except RequestException as e:
                    app.logger.warning(f"Failed to save data to DB: {e}")

        except RequestException as e:
            app.logger.error(f"External API error: {e}")
            if cached_data:
                app.logger.error(f"API fetch failed, and cache is expired.")

            return jsonify({"error": f"Failed to fetch data from external API: {e}"}), 503

    filtered_results = final_data

    if month:
        month = str(month).zfill(2)
        filtered_results = [holiday for holiday in filtered_results if holiday.get("month") == month]

    if name:
        filtered_results = [holiday for holiday in filtered_results if name.lower() in holiday.get("name", "").lower()]

    final_data = filtered_results 

    # Delete the cache time from the database
    for holiday in final_data:
        holiday.pop('cache_time', None)  

    if not final_data:
        return jsonify({
            "message": f"No holidays found for {country_upper} {year} with current filters.",
            "source": data_source,  
            "data": []
        }), 404

    return jsonify({
        "message": f"{country_upper} holiday data retrieved successfully",
        "country": country_upper,
        "year": year,
        "count": len(final_data),
        "source": data_source, 
        "data": final_data  
    }), 200


@app.route('/logic/holidays', methods=['GET'])
def holidays_endpoint():
    """
    API interface layer: Parses URL parameters and invokes underlying business functions.
    """
    country = request.args.get('country')   
    year = request.args.get('year')
    month = request.args.get('month')
    name = request.args.get('name')

    return get_holidays_data(country, year, month, name)


@app.route("/logic/test", methods=["GET"])
def test():
    return jsonify({"message": "r Group Logic Service is running"}), 200


if __name__ == '__main__':
    app.run(debug=True, port=5001)