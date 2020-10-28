import requests
import base64
import json
import certifi

# This is the main Python script file of klaviyo order sync. In the project folder you will find below structure,

# klaviyo_order_sync.py - main script file which you can schedule to run in every 30 min using scheduling tool (cron scheduler)

# last_order_number.txt - text file containing order number of the lastly synced order.
# last_order_time.txt - text file containing "created time" of the lastly synced order. We are keeping this record to stop multiple entries from the same order in klaviyo.

# When running this script as first time you should set values in this two files as below.

# last_order_number.txt ----> 0
# last_order_time.txt ------> 2020-01-08T12:53:07-05:00 (This is the "created time" of the oldest order in your store). 

# We need to set these two values only at the beginning to define the starting order. I already set these values for you so you don't need to set it again.


# pull_orders initiates the sync process
def pull_orders():
  # opening up the text file to retrieve the last date an order was created
  created_at_min = open('last_order_time.txt', 'r')

  # Sends a request to the Shopify Order API requesting all orders 
  response = requests.get(f'https://a9acc88bb9f836c23a6cb21e2b990964:c881e7f35a87ddd10d6aabe57c0ca2e6@success-engineering.myshopify.com/admin/api/2020-10/orders.json?created_at_min={created_at_min.read()}')

  # confirming that there were no errors with the request
  if response.status_code == 200:
    # closing the text file so nothing interferes with the file till it is needed next
    created_at_min.close()

    # turning the response into json
    json_response = response.json()

    # serialize the returned data to send to the Klaviyo API
    serialize_items(json_response)
  else:
    # error handling
    print('ERROR: ' + response.raise_for_status())

# We are pulling out only the necessary information to send to the klaviyo API for both metrics
def serialize_items(orders):
  # loop through the order for all the individual orders
  for order in orders["orders"]:
    order_number = order['number']

    last_order_number = open('last_order_number.txt', 'r')
    if order_number != last_order_number.read():

      # retrieve important information of a specific order (id, email, price, discounts etc.)
      order_name = order['name']
      order_id = order['id']
      email = order['email']
      created_at = order['created_at']
      total_price = order['total_price']
      total_discounts = order['total_discounts']
      source_name = order['source_name']
      line_items = order['line_items']
      item_count = len(line_items)

      # retrieving discounts codes of the order
      discount_codes = order['discount_codes']
      all_codes = []

      # looping through the discounts for the discount code and pushing it into its own array
      for code_item in discount_codes:
        code = code_item['code']
        all_codes.append(code)

      items_names = []

      # a given order can have multiple items. here we are going through those items one by one to sync with klaviyo
      for item in line_items:
        title = item['title']
        items_names.append(title)		
        price = item['price']
        variant_title = item['variant_title']
        sku = item['sku']
        product_id = item['product_id']
        fulfillable_quantity = item['fulfillable_quantity']

        # putting together the request to send to the metric "Ordered Product" with the following properties
        # price, title, variant_title, sku, product_id, fulfillable_quantity
        request = {
					"token": "WJ2uGm",
					"event": "Ordered Product",
					"customer_properties":{
							"email": email
					},
					"properties": {
						"Value": price,
						"Name": title,
						"VariantName": variant_title,
						"SKU": sku,
						"ProductID": product_id,
						"Quantity": fulfillable_quantity
					},
					"time": None
				}

        # turning the python object into json to send to the klaviyo api
        data = json.dumps(request).encode('utf-8')

        # since we are sending the object in the url as part of the string, we have to encrypt it using base64 encryption
        base64_data = base64.b64encode(data)

        # passing request data, tracking name and the order name to a function which makes the API call to klaviyo. You can find it at the bottom.
        callTrackAPI(base64_data, 'Ordered Product', order_name)
    
      # putting together the request to send to the metric "Ordered Product" with the following properties
      # total_price, items_names, item_count, discount_codes, total_discount, source_name
      request = {
					"token": "WJ2uGm",
					"event": "Placed Order",
					"customer_properties": {
							"email": email
					},
					"properties": {
						"Value": total_price,
						"Items": items_names,
						"ItemCount": item_count,
						"DiscountCodes": discount_codes,
						"TotalDiscounts": total_discounts,
						"SourceName": source_name,
						"tag": "Newsletter"
					},
					"time": None
				}

      # converting request data to JSON format
      data = json.dumps(request).encode('utf-8')

      # encoding json with base64 to send in the url
      base64_data = base64.b64encode(data)

      # calling callTrackAPI to send the placed order data to Klaviyo
      callTrackAPI(base64_data, 'Placed Order', order_name)

      # replacing order number in "last_order_time" text file by the order number of lastly synced order.
      created_at_min = open('last_order_time.txt', 'w+')

      # replacing the date time value in "last_order_time" text file by the created time of lastly synced order.
      last_order_number = open('last_order_number.txt', 'w+')

      # making the change in the file
      created_at_min.write(created_at)

      #closing the connection with the file
      created_at_min.close()

      # making the change in the file
      last_order_number.write(str(order_number))

      # making the change in the file
      last_order_number.close()

# // function which makes the API call to klaviyo by sending the content data on each metric
def callTrackAPI(base64_data_pram, metric, order_name):
  # API url
  track_api_url = 'https://a.klaviyo.com/api/track?data=' + base64_data_pram.decode("utf-8")
  
  # make a get request to the URL
  response = requests.get(track_api_url)

  if response.status_code == 200:
    # I added this only to show you the success state of each order sync.
    print('Added order ' + order_name + ' with metrics ' + metric + ' to klaviyo')
  else:
    # error handling
    print('ERROR: ', response.raise_for_status())

# calling pullOrders to begin the process of syncing the orders
pull_orders()