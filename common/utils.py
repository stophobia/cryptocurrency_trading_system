import os
import pybithumb
import pymysql
import sys
from datetime import datetime, timedelta
import traceback
import time
from pandas import DataFrame, Series
if os.name == 'nt':
    sys.path.append('C:\\source_code\\python\\cryptocurrency_trading_system')
    sys.path.append('C:\\source_code\\cryptocurrency_trading_system')

ymd_format = '%Y-%m-%d'


def create_conn(filepath: str) -> 'conn':
    """ Create DB connect func """
    import constant
    os.chdir(constant.ROOT_DIR)
    config = {}
    try:
        with open(filepath) as stream:
            for line in stream:
                k, v = line.strip().split('=')
                config[k] = v
        config['port'] = int(config['port'])
        conn = pymysql.connect(**config)
        return conn
    except FileNotFoundError:
        print('File Not Found!')


def log(msg, *args, **kwargs) -> None:
    now_tm = datetime.now()
    if args or kwargs:
        print(f'[{now_tm}] {msg} {args} {kwargs}')
    else:
        print(f'[{now_tm}] {msg}')


def mutation_db(sql: str, rows: tuple = None) -> None:
    conn = create_conn('.env')
    try:
        with conn.cursor() as cursor:
            cursor.execute(sql, rows)
            conn.commit()
    except Exception as e:
        log(f'DB mutation 예외발생 {str(e)}')
    except TimeoutError:
        print("mutation_db() TimeoutError, sleeping 1 minute.")
        time.sleep(60)
        mutation_db(sql, rows)
    finally:
        if conn:
            conn.close()


def mutation_many(sql: str, rows: tuple = None) -> None:
    conn = create_conn('.env')
    try:
        with conn.cursor() as cursor:
            cursor.executemany(sql, rows)
            conn.commit()
    except Exception as e:
        log(f'DB mutation 예외발생 {str(e)}')
    except TimeoutError:
        print("mutation_db() TimeoutError, sleeping 1 minute.")
        time.sleep(60)
        mutation_many(sql, rows)
    finally:
        if conn:
            conn.close()


def select_db(sql: str, rows: tuple = None) -> tuple:
    conn = create_conn('.env')
    try:
        with conn.cursor() as cursor:
            cursor.execute(sql, rows)
            return cursor.fetchall()
    except Exception as e:
        log(f'DB mutation 예외발생 {str(e)}')
    except TimeoutError:
        print("select_db() TimeoutError, sleeping 1 minute.")
        time.sleep(60)
        select_db(sql, rows)
    finally:
        if conn:
            conn.close()


def get_today_format(format: str = '%Y-%m-%d') -> str:
    today = datetime.today()
    today = today.strftime(format)
    return today



def calc_williams_R(ticker: str, R: float = 0.5) -> float:
    """
    래리 윌리엄스 변동성 돌파 계산하기
    :param ticker:
    :param R:
    :return: target_price
    """
    df: DataFrame = pybithumb.get_candlestick(ticker)
    # print(df.tail())
    if not df.empty:
        yesterday_s: Series = df.iloc[-2]
        today_s: Series = df.iloc[-1]
        today_open: Series = today_s['open']
        yesterday_high = yesterday_s['high']
        yesterday_low = yesterday_s['low']
        target_price = today_open + (yesterday_high - yesterday_low) * R
        return target_price
    return None


def calc_moving_average_by(ticker: str, days: int = 3) -> DataFrame:
    """
     days 이동평균 구하기 (당일 close  계산에 포함)
    """
    try:
        prices: DataFrame = pybithumb.get_candlestick(ticker)
        close: Series = prices['close']
        MA: Series = close.rolling(days).mean()
        # print(MA.tail())
        # 당일값 시세를 반영하려면 당일 close 가격이 포함된 당일 이동평균값 -1 사용!
        # 당일값 시세를 제외하려면 -2 전일 close 가격까지 포함된 전일 이동평균값 -2 사용
        ma_close_price = MA[-1]
        return ma_close_price
    except Exception as e:
        print(str(e))
        traceback.print_exc()


def calc_now_volatility(ticker: str) -> float:
    """ 당일 코인의 1일 변동성 계산
    :param ticker: 코인티커
       (당일고가 - 당일저가) / 시가  * 100
    """
    prices: 'df' = pybithumb.get_candlestick(ticker)
    if not prices.empty:
        row = prices.iloc[-1]
        open, high, low, close, volume = tuple(row)
        volatility = ((high - low) / open) * 100
        return round(volatility, 4)
    return None


def calc_prev_volatility(ticker: str) -> float:
    """ 전일 코인의 1일 변동성 계산
    :param ticker: 코인티커
       (당일고가 - 당일저가) / 시가  * 100
    """
    prices: 'df' = pybithumb.get_candlestick(ticker)
    if not prices.empty:
        row = prices.iloc[-2]
        open, high, low, close, volume = tuple(row)
        volatility = ((high - low) / open) * 100
        return round(volatility, 4)
    return None


def calc_average_volatility_by_days(ticker: str, days: int) -> float:
    """
    주어진 days 기간의 평균 변동성 계산
    :param ticker: 코인티커
    :param days: 기준 일수
    :return: days 기준 평균 변동성 값(%)
    """
    prices: 'DataFrame' = pybithumb.get_candlestick(ticker)
    if not prices.empty:
        rows = prices.iloc[days * -1:]
        volatility = ((rows['high'] - rows['low']) / rows['open']) * 100
        print(volatility)
        average = volatility.rolling(days).mean()
        print(average)
        return average[-1]
    return None


if __name__ == '__main__':
    conn = create_conn('.env')
    # print(conn)
    # print(get_today_format())

    print('비트코인 오늘 변동성: ', calc_now_volatility('BTC'))
    print('비트코인 전일 변동성: ', calc_prev_volatility('BTC'))
    print('이더리움 오늘 변동성', calc_now_volatility('ETH'))
    print('이더리움 전일 변동성', calc_prev_volatility('ETH'))
