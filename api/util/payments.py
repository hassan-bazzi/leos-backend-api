def normalize_price(price):
    if type(price) is int:
        price = str(price)
        leng = len(price)
        price = price[:leng-2] + '.' + price[leng-2:]
    return str(float(price))
