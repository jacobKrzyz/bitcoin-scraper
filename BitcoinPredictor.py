import sqlite3
import pandas as pd
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error, r2_score

# Function to read data from the database
def get_price_data():
    conn = sqlite3.connect('BITCOIN_price_history.db')
    df = pd.read_sql_query("SELECT * FROM prices", conn)
    conn.close()
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df = df.sort_values('timestamp')
    return df

# Function to prepare data for the model
def prepare_data(df):
    df['days_since_start'] = (df['timestamp'] - df['timestamp'].min()).dt.days
    X = df[['days_since_start']]
    y = df['price']
    return train_test_split(X, y, test_size=0.2, random_state=42)

# Function to train the model and make predictions
def train_and_predict(X_train, X_test, y_train, y_test):
    model = LinearRegression()
    model.fit(X_train, y_train)
    
    y_pred = model.predict(X_test)
    
    mse = mean_squared_error(y_test, y_pred)
    r2 = r2_score(y_test, y_pred)
    
    print(f"Mean squared error: {mse:.2f}")
    print(f"R-squared score: {r2:.2f}")
    
    return model

# Function to visualize the data and predictions
def visualize_predictions(df, model):
    plt.figure(figsize=(12, 6))
    plt.scatter(df['timestamp'], df['price'], color='blue', label='Actual Prices')
    
    future_dates = pd.date_range(start=df['timestamp'].max(), periods=30, freq='D')
    future_days = (future_dates - df['timestamp'].min()).days.values.reshape(-1, 1)
    future_prices = model.predict(future_days)
    
    plt.plot(future_dates, future_prices, color='red', label='Predicted Prices')
    plt.title('Bitcoin Price: Actual vs Predicted')
    plt.xlabel('Date')
    plt.ylabel('Price (USD)')
    plt.legend()
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.show()

# Function to predict price for a specific future date
def predict_future_price(model, df, days_in_future):
    last_date = df['timestamp'].max()
    future_date = last_date + timedelta(days=days_in_future)
    days_since_start = (future_date - df['timestamp'].min()).days
    predicted_price = model.predict([[days_since_start]])[0]
    return future_date, predicted_price

# Main function
def main():
    df = get_price_data()
    X_train, X_test, y_train, y_test = prepare_data(df)
    model = train_and_predict(X_train, X_test, y_train, y_test)
    
    # Get and print the current price
    current_price = df.iloc[-1]['price']
    current_date = df.iloc[-1]['timestamp']
    print(f"\nCurrent Bitcoin price as of {current_date}: ${current_price:.2f}")
    
    # Predict price for 3 days in the future
    future_date, predicted_price = predict_future_price(model, df, 3)
    percent_change = ((predicted_price - current_price) / current_price) * 100
    
    print(f"Predicted Bitcoin price for {future_date.date()}: ${predicted_price:.2f}")
    print(f"Predicted change: {percent_change:.2f}%")
    
    visualize_predictions(df, model)

if __name__ == "__main__":
    main()