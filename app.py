import sqlite3
from flask import Flask, request, Response
from twilio.twiml.messaging_response import MessagingResponse

app = Flask(__name__)

def get_product(product_name):
    conn = sqlite3.connect("shop.db")
    cursor = conn.cursor()

    cursor.execute(
        "SELECT name, price, stock FROM shop WHERE LOWER(name)=?",
        (product_name.lower(),)
    )

    result = cursor.fetchone()
    conn.close()

    if result:
        return {
            "name": result[0],
            "price": result[1],
            "stock": result[2]
        }

    return None


def get_all_products():
    conn = sqlite3.connect("shop.db")
    cursor = conn.cursor()

    cursor.execute("SELECT name FROM shop")
    results = cursor.fetchall()

    conn.close()

    return [row[0].lower() for row in results]


def extract_product(message):
    message_lower = message.lower()
    products = get_all_products()

    for product in products:
        if product in message_lower:
            return product

    return None


def handle_message(message):
    product = extract_product(message)

    if not product:
        return "Please specify a valid product available in our shop."

    item = get_product(product)

    if not item:
        return "Product not available"

    if item["stock"] > 0:
        return f"{item['name']} is available. Price: ₦{item['price']}. Stock: {item['stock']}"
    else:
        return f"{item['name']} is currently out of stock"


@app.route("/webhook", methods=["POST"])
def webhook():

    incoming_msg = request.form.get("Body")

    bot_response = handle_message(incoming_msg)

    resp = MessagingResponse()
    resp.message(bot_response)

    return Response(str(resp), mimetype="application/xml")


@app.route("/")
def home():
    return "Shop chatbot server is running!"


if __name__ == "__main__":
    app.run(port=5000, debug=True)