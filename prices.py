import requests

def get_all_prices_text():
    api_key = "freelJMthPmRumbJmopj7nTAwAyy6UQ7"
    url = f"http://api.navasan.tech/latest/?api_key={api_key}&item=usd_sell,usd_buy,18ayar"
    
    usd_text = "USD:\n❌ امکان دریافت قیمت دلار وجود ندارد\n"
    gold_text = "طلای ۱۸ عیار:\n❌ امکان دریافت قیمت طلا وجود ندارد\n"
    btc_text = "بیت‌کوین:\n - دلار: ❌ قابل دریافت نیست\n"

    try:
        data = requests.get(url).json()

        # دلار
        usd_sell = data.get("usd_sell", {})
        usd_buy = data.get("usd_buy", {})
        usd_sell_value = usd_sell.get("value", "N/A")
        usd_buy_value = usd_buy.get("value", "N/A")
        if usd_sell_value != "N/A" and usd_buy_value != "N/A":
            usd_text = (
                f"<b>دلار آمریکا:</b>\n"
                f"💵 فروش: {usd_sell_value} تومان\n"
                f"💵 خرید: {usd_buy_value} تومان\n"
            )
        else:
            usd_text = "<b>دلار آمریکا:</b>\n❌ قابل دریافت نیست\n"

        # طلا
        gold = data.get("18ayar", {})
        gold_value = gold.get("value", "N/A")
        gold_text = f"<b>طلای ۱۸ عیار:</b>\n🟨 {gold_value} تومان\n"

    except:
        pass

    try:
        btc_usd_res = requests.get(
            "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd"
        ).json()
        btc_usd_value = btc_usd_res.get("bitcoin", {}).get("usd", "N/A")
        btc_text = f"<b>بیت‌کوین:</b>\n🪙 {btc_usd_value} <b>دلار</b> ₿\n"
    except:
        pass

    return f"{usd_text}\n{gold_text}\n{btc_text}"
