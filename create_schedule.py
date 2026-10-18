
import csv
import calendar
from datetime import date, timedelta
from pathlib import Path

# 豆の種類
hot_beans = ["HOU", "CLG", "EDB", "SUM", "VER"]
iced_beans = ["HOU", "CLG"]

# CSVの保存先
data_dir = Path(__file__).resolve().parent / "data"
data_dir.mkdir(exist_ok=True)

# スケジュールの基準日
start_date = date(2026, 10, 1)
first_monday = date(2026, 9, 28)

# 2026年10月・11月のCSVを作成
for year, month in [(2026, 10), (2026, 11)]:

    days_in_month = calendar.monthrange(year, month)[1]
    file_path = data_dir / f"{year}-{month:02d}.csv"

    with open(file_path, "w", newline="", encoding="utf-8-sig") as file:
        writer = csv.writer(file)
        writer.writerow(["date", "hot", "iced"])

        for day in range(1, days_in_month + 1):
            current_date = date(year, month, day)

            # ホット：5種類を日替わり
            day_index = (current_date - start_date).days
            hot = hot_beans[day_index % len(hot_beans)]

            # アイス：月曜日に切り替え
            week_index = (current_date - first_monday).days // 7
            iced = iced_beans[week_index % len(iced_beans)]

            writer.writerow([current_date.isoformat(), hot, iced])

    print(f"作成完了：{file_path.name}")
