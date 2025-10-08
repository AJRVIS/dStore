# store/ai_module/predictor.py
import pandas as pd
from sklearn.linear_model import LinearRegression
from store.models import Transaction

def predict_next_week_sales():
    data = list(Transaction.objects.values("date", "total_price"))
    df = pd.DataFrame(data)
    if df.empty:
        return 0
    df["date"] = pd.to_datetime(df["date"])
    df["day"] = (df["date"] - df["date"].min()).dt.days
    X = df[["day"]]
    y = df["total_price"]
    model = LinearRegression()
    model.fit(X, y)
    next_week = df["day"].max() + 7
    predicted_sales = model.predict([[next_week]])[0]
    return round(predicted_sales, 2)
