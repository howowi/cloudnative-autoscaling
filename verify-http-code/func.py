import io
import logging
import requests
import json
from fdk import response


def handler(ctx, data: io.BytesIO = None):

    logging.getLogger().info("Start of Verify HTTP Code")
    
    try:
        body = json.loads(data.getvalue())
        url = body.get("url")
        resp = requests.head(url)
        if resp.status_code == 200:
            logging.getLogger().info(url + " is accessible")
            result = 'true'
            return result.encode()
        else:
            logging.getLogger().info(url + " is not accessible")
            result = 'false'
            return result.encode()

    except requests.exceptions.ConnectionError:
        logging.getLogger().info("Connection Error")
        result = 'false'
        return result.encode()
