import stocklab
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.dates import date2num, DateFormatter
from mplfinance.original_flavor import candlestick_ohlc

LARGE_NUM = 5000

def plot(dates, ohlc, signs=None, aux={}, top_aux={}, side_aux={}):
  dates = np.array([date2num(d.datetime) for d in dates])
  ohlc = np.array(ohlc)

  plt.rc('axes', grid=True)
  plt.rc('grid', color='0.75', linestyle='-', linewidth=0.5)

  fig = plt.figure(facecolor='white')
  gs = fig.add_gridspec(3, 3)
  assert not side_aux, 'Not implemented yet' # TODO
  if top_aux:
    ax = fig.add_subplot(gs[1:, :])
    plt.setp(plt.gca().get_xticklabels(), rotation=45, horizontalalignment='right')
    axt = fig.add_subplot(gs[0, :], sharex=ax)
    plt.setp(plt.gca().get_xticklabels(), color='w')
  else:
    ax = fig.add_subplot(gs[:, :])
    plt.setp(plt.gca().get_xticklabels(), rotation=45, horizontalalignment='right')

  ax.xaxis.set_major_formatter(DateFormatter('%F'))
  ax.set_ylim(ohlc[:,2].min(), ohlc[:,1].max())
  ax.xaxis_date()
  ax.autoscale_view()
  
  candlestick_ohlc(ax, np.hstack((dates[:,np.newaxis], ohlc)),
      width=0.5, colorup='r', colordown='green', alpha=0.6)

  for k, v in top_aux.items():
    v = np.array(v)
    axt.plot(dates, v, label=k, drawstyle='steps-post')
  if aux:
    axt.legend(loc='upper left')

  for k, v in aux.items():
    v = np.array(v)
    ax.plot(dates, v, label=k, drawstyle='steps-post')
  if aux:
    ax.legend(loc='upper left')
  
  def interleave(a, b):
    retval = np.empty((len(a) + len(b),), dtype=a.dtype)
    retval[0::2] = a
    retval[1::2] = b
    return retval
  
  if signs is not None:
    signs = np.array(signs)
    int_idx = interleave(
        dates,
        dates + 1
        )
    bull_sign = signs == 1
    bear_sign = signs == -1
    ax.fill_between(int_idx, LARGE_NUM,
            where=interleave(bull_sign, bull_sign),
            facecolor='green', alpha=0.2)
    ax.fill_between(int_idx, LARGE_NUM,
            where=interleave(bear_sign, bear_sign),
            facecolor='red', alpha=0.2)
  plt.show()

def simulate(dates, signs, prices, verbose=False):
  def _sim(dates, signs, prices, balance=0, cost=None, sell_th=None):
    date = dates[0]
    price = prices[0]
    sign = signs[0]
    if len(dates) == 1:
      if cost:
        if verbose:
          print(f'[{date}] sell (terminate) @ {price} (gain: {price-cost:.3})')
        return balance + price
      else:
        return balance
    else:
      if sell_th and cost and price - cost > sell_th:
        if verbose:
          print(f'[{date}] sell (over threshold) @ {price} (gain: {price-cost:.3})')
        return _sim(dates[1:], signs[1:], prices[1:], balance + price, None, sell_th)
      elif 1 == sign and not cost:
        if verbose:
          print(f'[{date}] buy @ {price}')
        return _sim(dates[1:], signs[1:], prices[1:], balance - price, price, sell_th)
      elif -1 == sign and cost:
        if verbose:
          print(f'[{date}] sell @ {price} (gain: {price-cost:.3})')
        return _sim(dates[1:], signs[1:], prices[1:], balance + price, None, sell_th)
      else:
        return _sim(dates[1:], signs[1:], prices[1:], balance, cost, sell_th)
  return _sim(dates, signs, prices)

def random_simulate(date, days, dates_expr, ohlc_expr, sign_expr, stocks_expr=None, verbose=False):
  dates_expr = dates_expr(date, days)
  dates = stocklab.metaevaluate(dates_expr)
  if not stocks_expr:
    stocks_expr = stocklab.config['stocks_of_interest']

  stocks = np.array(list(stocklab.metaevaluate(stocks_expr)))
  np.random.shuffle(stocks)

  def _sim(stock_id):
    ohlcs = np.array(stocklab.evaluate(ohlc_expr(stock_id, f'(${dates_expr})')))
    prices = ohlcs[:,3]
    signs = stocklab.evaluate(sign_expr(stock_id, f'(${dates_expr})'))
    return simulate(dates, signs, prices, verbose)

  for sid in stocks:
    yield sid, _sim(sid)