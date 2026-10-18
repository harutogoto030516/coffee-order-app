
import math
import csv
import jpholiday

from pathlib import Path
from datetime import datetime, timedelta
from flask import Flask, render_template, request


# =====================================
# 1. 基本設定
# =====================================

app = Flask(__name__)

beans = ["HOU", "CLG", "EDB", "SUM", "VER"]

max_stock = 20

USAGE = {
    "hot": {
        "weekday": 12,
        "holiday": 10
    },
    "iced": {
        "weekday": 8,
        "holiday": 6
    }
}

DATA_DIR = Path(__file__).resolve().parent / "data"

# 発注曜日と納品までの日数
# 火曜 → 木曜、木曜 → 土曜、日曜 → 火曜
delivery_days = {
    1: 2,
    3: 2,
    6: 2
}


# =====================================
# 2. 発注数の計算
# =====================================

def calculate_order(current_stock, expected_usage):

    order = max_stock - current_stock + expected_usage

    order = math.ceil(order)

    # 発注数は0〜20袋
    order = max(0, min(20, order))

    return order


# =====================================
# 3. 納品日の取得
# =====================================

def get_delivery_date(order_date):

    weekday = order_date.weekday()

    if weekday not in delivery_days:
        return None

    return order_date + timedelta(
        days=delivery_days[weekday]
    )


# =====================================
# 4. CSVから使用予定を取得
# =====================================

def get_schedule(target_date):

    file_path = DATA_DIR / f"{target_date:%Y-%m}.csv"

    with open(
        file_path,
        encoding="utf-8-sig",
        newline=""
    ) as file:

        reader = csv.DictReader(file)

        for row in reader:
            if row["date"] == target_date.isoformat():
                return row

    raise ValueError(
        f"使用予定が見つかりません：{target_date}"
    )


# =====================================
# 5. 納品までの予想使用量を計算
# =====================================

def calculate_expected_usage(order_date):

    delivery_date = get_delivery_date(order_date)

    if delivery_date is None:
        raise ValueError("発注日ではありません")

    usage_by_bean = {
        bean: 0 for bean in beans
    }

    # 翌日の全使用量 ＋ 納品日の午前使用量
    for target_date, fraction in [
        (order_date.date() + timedelta(days=1), 1.0),
        (delivery_date.date(), 0.5)
    ]:

        schedule = get_schedule(target_date)

        is_holiday = (
            target_date.weekday() >= 5
            or jpholiday.is_holiday(target_date)
        )

        day_type = (
            "holiday" if is_holiday else "weekday"
        )

        hot_bean = schedule["hot"]
        iced_bean = schedule["iced"]

        usage_by_bean[hot_bean] += (
            USAGE["hot"][day_type] * fraction
        )

        usage_by_bean[iced_bean] += (
            USAGE["iced"][day_type] * fraction
        )

    return usage_by_bean


# =====================================
# 6. 5種類の豆の発注数を一括計算
# =====================================

def calculate_all_orders(order_date, current_stocks):

    expected_usage = calculate_expected_usage(order_date)

    orders = {}

    for bean in beans:

        orders[bean] = calculate_order(
            current_stocks[bean],
            expected_usage[bean]
        )

    return orders


# =====================================
# 7. Flask Webアプリ
# =====================================

@app.route("/", methods=["GET", "POST"])
def index():

    today = datetime.today().date()

    selected_date = today

    current_stocks = {
        bean: 0 for bean in beans
    }

    orders = None
    expected_usage = None
    delivery_date = None
    error = None

    if request.method == "POST":

        try:
            # 画面で選択した発注日
            selected_date = datetime.strptime(
                request.form["order_date"],
                "%Y-%m-%d"
            ).date()

            order_date = datetime.combine(
                selected_date,
                datetime.min.time()
            )

            # 画面で入力した現在庫数
            current_stocks = {
                bean: int(request.form[bean])
                for bean in beans
            }

            # 在庫数の入力チェック
            if any(
                stock < 0 or stock > max_stock
                for stock in current_stocks.values()
            ):
                raise ValueError(
                    "現在庫数は0〜20袋で入力してください"
                )

            # 納品日の取得
            delivery_date = get_delivery_date(order_date)

            if delivery_date is None:
                raise ValueError(
                    "火曜日・木曜日・日曜日を選択してください"
                )

            # 予想使用量と発注数を計算
            expected_usage = calculate_expected_usage(
                order_date
            )

            orders = calculate_all_orders(
                order_date,
                current_stocks
            )

        except (
            ValueError,
            KeyError,
            FileNotFoundError
        ) as e:

            error = str(e)

    return render_template(
        "index.html",
        beans=beans,
        selected_date=selected_date.isoformat(),
        current_stocks=current_stocks,
        orders=orders,
        expected_usage=expected_usage,
        delivery_date=delivery_date,
        error=error
    )


# =====================================
# 8. アプリの起動
# =====================================

if __name__ == "__main__":
    app.run(debug=True)
