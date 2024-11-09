import requests
import time
from datetime import datetime, timedelta
import sqlite3
import pytz

def create_table():
    conn = sqlite3.connect('BITCOIN_price_history.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS prices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            price REAL,
            timestamp DATETIME UNIQUE
        )
    ''')
    conn.commit()
    conn.close()

def insert_price(price, timestamp):
    conn = sqlite3.connect('BITCOIN_price_history.db')
    cursor = conn.cursor()
    try:
        cursor.execute('INSERT INTO prices (price, timestamp) VALUES (?, ?)', (price, timestamp))
        conn.commit()
        print(f"Inserted: ${price:.2f} at {timestamp}")
        return True
    except sqlite3.IntegrityError:
        cursor.execute('SELECT price FROM prices WHERE timestamp = ?', (timestamp,))
        existing_price = cursor.fetchone()[0]
        print(f"Price for {timestamp} already exists in the database: ${existing_price:.2f}")
        return False
    finally:
        conn.close()

def get_hourly_price(timestamp):
    unix_timestamp = int(timestamp.timestamp())
    url = f"https://api.coingecko.com/api/v3/coins/bitcoin/market_chart/range?vs_currency=usd&from={unix_timestamp-3600}&to={unix_timestamp+3600}"
    response = requests.get(url)
    data = response.json()
    if 'prices' not in data or not data['prices']:
        raise ValueError("No price data available for this timestamp")
    closest_price = min(data['prices'], key=lambda x: abs(x[0]/1000 - unix_timestamp))
    return closest_price[1]

def populate_historical_data():
    est = pytz.timezone('US/Eastern')
    end_date = datetime.now(est).replace(hour=0, minute=0, second=0, microsecond=0)
    start_date = end_date - timedelta(days=90)  # 3 months

    current_date = start_date
    data_points_added = 0

    while current_date <= end_date:
        for hour in [11, 16]:  # 11am and 4pm
            timestamp = current_date.replace(hour=hour, minute=0, second=0, microsecond=0)
            if timestamp <= end_date:
                retry_count = 0
                while retry_count < 3:  # Try up to 3 times
                    try:
                        price = get_hourly_price(timestamp)
                        if insert_price(price, timestamp):
                            data_points_added += 1
                        break  # Exit the retry loop if successful
                    except ValueError as e:
                        print(f"No price found for {timestamp}: {e}")
                        print("Pausing for 60 seconds before retrying...")
                        time.sleep(60)
                        retry_count += 1
                    except Exception as e:
                        print(f"Unexpected error for {timestamp}: {e}")
                        break  # Exit the retry loop for unexpected errors

                if data_points_added % 5 == 0 and data_points_added > 0:
                    print(f"Added {data_points_added} new data points. Pausing for 60 seconds due to API limit...")
                    time.sleep(60)  # Pause for 60 seconds after every 5 data points

        current_date += timedelta(days=1)

def main():
    create_table()
    populate_historical_data()
    print("Historical data population completed.")

if __name__ == "__main__":
    main()