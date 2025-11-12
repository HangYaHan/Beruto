# filename: fetch_data.py
import akshare as ak
import seaborn as sns
import pandas as pd
import matplotlib.pyplot as plt
import os

# ========= 参数部分 =========
symbol = "sh600000"      # 股票代码，比如 "sh600000"（浦发银行）
start_date = "20200101"  # 开始日期
end_date = "20251112"    # 结束日期      
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) # 存放数据在根目录的data文件夹
save_dir = os.path.join(root_dir, "data")
# ============================

# 创建data文件夹（如果没有）
os.makedirs(save_dir, exist_ok=True)

# 拉取日线数据
df = ak.stock_zh_a_daily(symbol=symbol, start_date=start_date, end_date=end_date)

# 保存数据
file_path = os.path.join(save_dir, f"{symbol}.csv")
df.to_csv(file_path, index=False, encoding="utf-8-sig")
print(f"数据已保存到 {file_path}")


# 画图（收盘价）
df["date"] = pd.to_datetime(df["date"])
plt.figure(figsize=(10, 5))
sns.lineplot(x=df["date"], y=df["close"], label='closing price')
plt.title(f"{symbol} closing price trend")
plt.xlabel("Date")
plt.ylabel("Closing Price (CNY)")
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.show()

