from datetime import datetime
from tronapi import Tron


def hex_to_base58(hex_str: str, tron: Tron):
    """ Convert hex string to Tron's base58 address. """
    # Use Tron's address property for conversion
    return tron.address.from_hex(hex_str).decode('utf-8')


def extract_transaction_details(transaction_json: dict, tron: Tron) -> dict:
    """This function extracts transaction details from raw transaction data
    It returns the following dictionary:

        return {
        'transaction_id': transaction_id,
        'sender_address': sender_address,
        'contract_address': contract_address,
        'receiver_address': receiver_address,
        'value': value,
        'timestamp': timestamp
    }"""

    # Extracting fields from JSON
    try:
        contract_info = transaction_json['raw_data']['contract'][0]['parameter']['value']
        owner_address_hex = contract_info['owner_address']
        contract_address_hex = contract_info['contract_address']
        data_hex = contract_info['data']
        transaction_id = transaction_json['txID']
        # Division is necessary to convert milliseconds to seconds.
        timestamp = float(transaction_json['raw_data']['timestamp']) / 1000
    except KeyError:
        # A transaction is most likely not a token transfer.
        return None

    # Decode hex to base58 for addresses
    sender_address = hex_to_base58(owner_address_hex, tron)
    contract_address = hex_to_base58(contract_address_hex, tron)

    # Extract receiver address and value from data
    # Skipping first 10 bytes (method ID), next 32 bytes are the receiver address
    receiver_address_hex = "41" + data_hex[32:72]
    receiver_address = hex_to_base58(receiver_address_hex, tron)

    # Last 32 bytes are the value (in hex)
    value_hex = data_hex[72:]
    value = tron.fromSun(int(value_hex, 16))

    # Convert timestamp to UTC
    # timestamp_utc = datetime.utcfromtimestamp(
    #     timestamp / 1000).strftime('%Y-%m-%d %H:%M:%S')

    return {
        'transaction_id': transaction_id,
        'sender_address': sender_address,
        'contract_address': contract_address,
        'receiver_address': receiver_address,
        'value': value,
        'timestamp': timestamp
    }
