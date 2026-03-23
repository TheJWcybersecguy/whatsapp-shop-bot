import sqlite3
import re
import os
from flask import Flask, request, Response
from twilio.twiml.messaging_response import MessagingResponse

app = Flask(__name__)

# --------------------------
# Helper function to normalize text for matching
# --------------------------
def normalize(text):
    """Lowercase and remove special characters except letters, numbers, spaces."""
    return re.sub(r'[^a-z0-9\s]', '', text.lower())

# --------------------------
# Get a single product from the database
# --------------------------
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
        return {"name": result[0], "available": result[1]}
    return None

# --------------------------
# Get all products from the database
# --------------------------
def get_all_products():
    conn = sqlite3.connect("shop.db")
    cursor = conn.cursor()

    cursor.execute("SELECT name, available FROM shop")
    results = cursor.fetchall()
    conn.close()

    # Return list of tuples (name, available)
    return results

# --------------------------
# Extract products from message
# --------------------------
def extract_products(message):
    """
    Return a list of products whose names partially match any keyword in message.
    """
    normalized_msg = normalize(message)
    all_products = get_all_products()

    matched_products = []

    for product_name, available in all_products:
        normalized_product = normalize(product_name)
        # Check if any word in the message is in the product name
        if any(word in normalized_product for word in normalized_msg.split()):
            matched_products.append((product_name, available))

    # Debug
    if matched_products:
        print(f"Matched products for message '{message}': {matched_products}")
    else:
        print(f"No product matched for message: '{message}'")

    return matched_products

# --------------------------
# Handle incoming message
# --------------------------
def handle_message(message):
    matched_products = extract_products(message)

    if not matched_products:
        return "Please specify a valid product available in our shop."

    responses = []
    for name, available in matched_products:
        if available < 1:
            responses.append(f"{name} is currently NOT available.")
        else:
            responses.append(f"{name} is available in stock.")

    return "\n".join(responses)

# --------------------------
# Flask webhook route for Twilio
# --------------------------
@app.route("/webhook", methods=["POST"])
def webhook():
    incoming_msg = request.form.get("Body", "")
    bot_response = handle_message(incoming_msg)

    resp = MessagingResponse()
    resp.message(bot_response)

    return Response(str(resp), mimetype="application/xml")

# --------------------------
# Simple home route
# --------------------------
@app.route("/")
def home():
    return "Shop chatbot server is running!"

# --------------------------
# Main app run
# --------------------------
if __name__ == "__main__":
    # Debug: print first 5 products
    conn = sqlite3.connect("shop.db")
    cursor = conn.cursor()
    cursor.execute("SELECT name, available FROM shop LIMIT 5")
    rows = cursor.fetchall()
    conn.close()
    print("First 5 products in shop.db on startup:")
    for row in rows:
        print(row)

    # Use PORT env variable for Render deployment
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)