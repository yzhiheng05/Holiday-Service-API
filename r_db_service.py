from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from sqlalchemy.exc import SQLAlchemyError

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = f"mysql+pymysql://Hua123456:abc137814@Hua123456.mysql.pythonanywhere-services.com/Hua123456$default"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

# Database Model Definition
class PublicHoliday(db.Model):
    __tablename__ = 'public_holidays'

    date = db.Column(db.String(10), nullable=False)
    countryCode = db.Column(db.String(2), nullable=False)
    month = db.Column(db.String(2), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    cache_time = db.Column(db.DateTime, nullable=False)     # Record the current cache time

    __table_args__ = (db.PrimaryKeyConstraint('date', 'countryCode'),)

# Save/Update Data (POST)
def save_country(holiday_list, code):
    if not holiday_list:
        return jsonify({"error": "No valid data received, please check if the request body is a JSON list (must contain date, month, name)"}), 400
    try:
        for holiday in holiday_list:
            # Merging old and new data
            db.session.merge(PublicHoliday(
                date=holiday['date'],
                countryCode=code,
                month=str(holiday['month']).zfill(2),
                name=holiday['name'],
                cache_time=datetime.now()
            ))
        db.session.commit()         # Commit data to the database
        return jsonify({"message": f"{code} Holiday data saved/updated successfully", "count": len(holiday_list)}), 201
    except SQLAlchemyError:
        db.session.rollback()       # Rollback when database error
        return jsonify({"error": f"Failed to save {code} holiday data to database."}), 500

@app.route('/db/save-china', methods=['POST'])
def save_cn():
    return save_country(request.json, 'CN')

@app.route('/db/save-ireland', methods=['POST'])
def save_ie():
    return save_country(request.json, 'IE')

# Search data (GET)
def get_country(code, year):
    # Find holiday by countrycode
    query = PublicHoliday.query.filter_by(countryCode=code)
    # Find holiday by year
    if year:
        query = query.filter(PublicHoliday.date.like(f'{year}%'))
    holiday_list = query.all()
    result = []     # Created an empty list
    for holiday in holiday_list:
        result.append({
            "date": holiday.date,
            "countryCode": holiday.countryCode,
            "month": holiday.month,
            "name": holiday.name,
            "cache_time": holiday.cache_time.strftime("%Y-%m-%d %H:%M:%S")
        })
    if len(holiday_list) == 0:
        return jsonify({"error": f"No holiday data found for {code} in {year}"}), 404
    return jsonify(
        {"message": f"{code} holiday data get successfully", "count": len(holiday_list), "data": result}), 200

@app.route('/db/get-china', methods=['GET'])
def get_cn():
    return get_country('CN', request.args.get('year'))

@app.route('/db/get-ireland', methods=['GET'])
def get_ie():
    return get_country('IE', request.args.get('year'))

# test
@app.route('/test')
def home():
    return 'r Group Holiday DB SQLAlchemy OK'

if __name__ == '__main__':
    app.run(debug=True)