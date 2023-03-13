from binance.client import Client
import pandas as pd
import time
from datetime import datetime, timedelta

# import matplotlib.pyplot as plt

btc_symbol = 'BTCUSDT'
eth_symbol = 'ETHUSDT'

percent_change = 1.0
interval = '1m'

# Определяем временные рамки для получения данных (60 минут назад до текущего момента).
# За сутки коэффициент точнее, но так как это тест, за час более показательны движения.
end_time = int(datetime.now().timestamp() * 1000)
start_time = end_time - 60 * 60 * 1000

client = Client()

# Получаем историю фьючерсов
eth_klines = client.futures_historical_klines(eth_symbol, interval, start_time, end_time)
btc_klines = client.futures_historical_klines(btc_symbol, interval, start_time, end_time)

# Преобразуем данные в pandas dataframe
eth_df = pd.DataFrame(eth_klines, columns=["timestamp", "open", "high", "low", "close", "volume", "close_time",
                                           "quote_asset_volume", "number_of_trades", "taker_buy_base_asset_volume",
                                           "taker_buy_quote_asset_volume", "ignore"])
btc_df = pd.DataFrame(btc_klines, columns=["timestamp", "open", "high", "low", "close", "volume", "close_time",
                                           "quote_asset_volume", "number_of_trades", "taker_buy_base_asset_volume",
                                           "taker_buy_quote_asset_volume", "ignore"])

# Удаляем лишние столбцы
eth_df.drop(columns=["open", "high", "low", "volume", "close_time", "quote_asset_volume", "number_of_trades",
                     "taker_buy_base_asset_volume", "taker_buy_quote_asset_volume", "ignore"], inplace=True)
btc_df.drop(columns=["open", "high", "low", "volume", "close_time", "quote_asset_volume", "number_of_trades",
                     "taker_buy_base_asset_volume", "taker_buy_quote_asset_volume", "ignore"], inplace=True)

# Приводим даты к формату datetime
eth_df["timestamp"] = pd.to_datetime(eth_df["timestamp"], unit="ms")
btc_df["timestamp"] = pd.to_datetime(btc_df["timestamp"], unit="ms")
# приводим цены к числовому формату
btc_df['close'] = pd.to_numeric(btc_df['close'])
eth_df['close'] = pd.to_numeric(eth_df['close'])

# Объединяем данные по времени
merged_df = pd.merge(eth_df, btc_df, on="timestamp")

# Вычисляем коэффициент корреляции между ценами ETHUSDT и BTCUSDT
corr_coefficient = merged_df["close_x"].corr(merged_df["close_y"])

print(f'Коэффициент корреляции: {corr_coefficient}')

# # Построение графика собственного изменения цен ETHUSDT
# eth_df['close'] = eth_df['close'] - corr_coefficient * eth_df['close']
#
# plt.plot(eth_df['close'])
# plt.xlabel('Time')
# plt.ylabel('Price')
# plt.title('Изменение собственной цены ETHUSDT (без учета BTCUSDT)')
# plt.show()

if __name__ == '__main__':
    while True:
        try:
            # Получение текущей цены фьючерса ETHUSDT
            current_price = float(client.futures_symbol_ticker(symbol=eth_symbol)['price'])

            # Получение цены закрытия из последней свечи час назад
            start_time = int((datetime.now() - timedelta(hours=1)).timestamp() * 1000)
            end_time = start_time + 60000

            history = client.futures_historical_klines(eth_symbol, interval, start_time, end_time, limit=1)
            prev_price = float(history[0][4])

            # Вычисление собственных движений цены фьючерса ETHUSDT
            own_price = current_price - (corr_coefficient * current_price)
            prev_own_price = prev_price - (corr_coefficient * prev_price)

            # Изменение собственной цены за последние 60 минут
            price_change = (own_price - prev_own_price) / prev_own_price * 100

            if abs(price_change) >= percent_change:
                print(f'{datetime.now().strftime("%Y-%m-%d %H.%M.%S")}: '
                      f'собственная цена изменилась на {price_change:.2f}% за последние 60 минут')

            # Ждем 1 секунду, чтобы не нагружать сервер binance
            time.sleep(1)

        except Exception as e:
            print(e)
            time.sleep(5)
