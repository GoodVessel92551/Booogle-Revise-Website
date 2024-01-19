import os
from flask import Flask, redirect, request,jsonify
from flask.templating import render_template

import stripe
from stripe.error import StripeError

stripe.api_key = os.environ['PAY_API']
endpoint_secret = os.environ['WEB_HOOK']

# Username
name = "Name"

app = Flask(__name__,
            static_url_path='',
            static_folder='public')

YOUR_DOMAIN = 'https://a09f49b2-87b4-4176-bd87-3a2933438507-00-2phsjujlyub5c.kirk.replit.dev/'

@app.route("/")
def index():
    return render_template("checkout.html")

@app.route('/create-checkout-session', methods=['POST'])
def create_checkout_session():
    try:
        checkout_session = stripe.checkout.Session.create(
            line_items=[
                {
                    # Provide the exact Price ID (for example, pr_1234) of the product you want to sell
                    'price': 'price_1O42nmEg9DaDrNLanEjHmmf3',
                    'quantity': 1,
                },
            ],
            mode='payment',
            success_url=YOUR_DOMAIN + '/success.html',
            cancel_url=YOUR_DOMAIN + '/cancel.html',
            metadata = {
                "name":name
            },
        )
    except Exception as e:
        return str(e)
    return redirect(checkout_session.url, code=303)


@app.route('/webhook', methods=['POST'])
def webhook():
    event = None
    payload = request.data
    sig_header = request.headers['STRIPE_SIGNATURE']
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, endpoint_secret
        )
    except ValueError as e:
        raise e

    except stripe.error.SignatureVerificationError as e:
        raise e

    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        if session["payment_status"] == "paid":
            print("User:",session["metadata"]["name"])
    else:
        print('Unhandled event type {}'.format(event['type']))
    return True

app.run(host="0.0.0.0",port=8080,debug=True)