import sqlite3
import re
from flask import Flask, request, Response
from twilio.twiml.messaging_response import MessagingResponse

app = Flask(__name__)

# Helper function to normalize text for matching
def normalize(text):
    # Lowercase and remove special characters except letters, numbers, and spaces
    return re.sub(r'[^a-z0-9\s]', '', text.lower())

# Get a single product from the database
def get_product(product_name):
    conn = sqlite3.connect("shop.db")
    cursor = conn.cursor()

    cursor.execute(
        "SELECT name, available FROM shop WHERE LOWER(name)=?",
        (product_name.lower(),)
    )

    result = cursor.fetchone()
    conn.close()

    if result:
        return {
            "name": result[0],
            "available": result[1]
        }

    return None

# Get all product names from the database
def get_all_products():
    conn = sqlite3.connect("shop.db")
    cursor = conn.cursor()

    cursor.execute("SELECT name, available FROM shop")
    results = cursor.fetchall()
    conn.close()

    # Return original names for matching
    return [row[0] for row in results]

# Extract all products from the incoming message with normalization
def extract_products(message):
    normalized_msg = normalize(message)
    products = get_all_products()

    matched_products = []

    for product in products:
        normalized_product = normalize(product)
        # Check if any word in the product name is in the message
        for word in normalized_product.split():
            if word in normalized_msg and product not in matched_products:
                matched_products.append(product)

    # Debug print
    if matched_products:
        print(f"Matched products for message '{message}': {matched_products}")
    else:
        print(f"No product matched for message: '{message}'")

    return matched_products

# Handle incoming message and generate response
def handle_message(message):
    products = extract_products(message)

    if not products:
        return "Please specify a valid product available in our shop."

    responses = []
    for product in products:
        item = get_product(product)
        if item and item["available"]:
            responses.append(f"{item['name']} is available in stock.")
        elif item:
            responses.append(f"{item['name']} is currently out of stock.")

    return "\n".join(responses)

# Flask route for Twilio webhook
@app.route("/webhook", methods=["POST"])
def webhook():
    incoming_msg = request.form.get("Body")
    bot_response = handle_message(incoming_msg)

    resp = MessagingResponse()
    resp.message(bot_response)

    return Response(str(resp), mimetype="application/xml")

# Simple home route
@app.route("/")
def home():
    return "Shop chatbot server is running!"

# Run the Flask app
if __name__ == "__main__":
    # Debug: print first few products on startup to confirm database
    conn = sqlite3.connect("shop.db")
    cursor = conn.cursor()
    cursor.execute("SELECT name, available FROM shop LIMIT 5")
    rows = cursor.fetchall()
    conn.close()
    print("First 5 products in shop.db on startup:")
    for row in rows:
        print(row)

    app.run(port=5000, debug=True)