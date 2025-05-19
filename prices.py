import requests


def get_all_prices_text():
    
    api_key = "freelJMthPmRumbJmopj7nTAwAyy6UQ7"
    url = f"http://api.navasan.tech/latest/?api_key={api_key}&item=usd_sell,usd_buy,18ayar"
    usd_text = "USD:\n❌ امکان دریافت قیمت دلار وجود ندارد\n"
    gold_text = "طلای ۱۸ عیار:\n❌ امکان دریافت قیمت طلا وجود ندارد\n"
    btc_text = "بیت‌کوین:\n - دلار: ❌ قابل دریافت نیست\n"

    # گرفتن داده‌های نواسان
    try:
        data = requests.get(url).json()

        # دلار
        usd_sell = data.get("usd_sell", {})
        usd_buy = data.get("usd_buy", {})
        usd_sell_value = usd_sell.get("value", "N/A")
        usd_sell_date = usd_sell.get("date", "N/A")
        usd_buy_value = usd_buy.get("value", "N/A")
        usd_buy_date = usd_buy.get("date", "N/A")
        usd_text = (
            f"USD:\n"
            f"فروش: {usd_sell_value} تومان ({usd_sell_date})💵\n"
            f"خرید: {usd_buy_value} تومان ({usd_buy_date})💵\n"
        )

        # طلا
        gold = data.get("18ayar", {})
        gold_value = gold.get("value", "N/A")
        gold_date = gold.get("date", "N/A")
        gold_text = f"طلای ۱۸ عیار:\nقیمت: {gold_value} تومان ({gold_date})🪙\n"

    except:
        pass  # خطاهای نواسان

    # گرفتن قیمت بیت‌کوین به دلار از کوین‌گکو
    try:
        btc_usd_res = requests.get(
            "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd"
        ).json()
        btc_usd_value = btc_usd_res.get("bitcoin", {}).get("usd", "N/A")
        btc_text = f"بیت‌کوین:\n - دلار: {btc_usd_value} دلار (زنده) ₿\n"
    except:
        pass  # خطای دریافت بیت‌کوین

    return f"{usd_text}\n{gold_text}\n{btc_text}"

# استفاده:
print(get_all_prices_text())
