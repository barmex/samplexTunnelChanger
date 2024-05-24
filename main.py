from flask import Flask, request
from flask_basicauth import BasicAuth
import logging
import os
import requests
from requests.auth import HTTPBasicAuth

webUsername = os.environ['WEBUSERNAME']
webPassword = os.environ['WEBPASSWORD']
routerHost = os.environ['ROUTERHOST']
routerPort = os.environ['ROUTERPORT']
routerUsername = os.environ['ROUTERUSERNAME']
routerPassword = os.environ['ROUTERPASSWORD']
tgBotToken = os.environ['BOTTOKEN']
tgChatID = os.environ['BOTCHATID']

requests.packages.urllib3.disable_warnings()

app = Flask(__name__)
app.config['BASIC_AUTH_USERNAME'] = webUsername
app.config['BASIC_AUTH_PASSWORD'] = webPassword
basic_auth = BasicAuth(app)


@app.route('/get_current_state', methods=['GET'])
@basic_auth.required
def get_current_state():
    param = request.get_json(force=True)
    routerInterfaceIndex = param.get('interfaceIndex')
    if routerInterfaceIndex:
        response = get_current_interface_state(routerHost, routerPort, routerUsername, routerPassword,
                                               routerInterfaceIndex)
        logging.debug(response)
        logging.debug(response.text)
        return response.text, response.status_code


@app.route('/change_tunnel_interface', methods=['POST'])
@basic_auth.required
def change_tunnel_interface():
    data = request.get_json(force=True)
    routerInterfaceIndex = data.get('interfaceIndex')
    ipAddress = data.get('ipAddress')
    if routerInterfaceIndex and ipAddress:
        response = set_tunnel_interface_destination_ip_address(routerHost, routerPort, routerUsername, routerPassword,
                                                               routerInterfaceIndex, ipAddress=ipAddress)
        return response.text, response.status_code
    else:
        return 'Wrong parameters interfaceIndex or ipAddress.', 500


def get_current_interface_state(routerHost: str, routerPort: int, routerUsername: str, routerPassword: str,
                                routerInterfaceIndex: str) -> dict:
    url = f'https://{routerHost}:{routerPort}/restconf/data/Cisco-IOS-XE-native:native/interface/Tunnel={routerInterfaceIndex}/'
    headers = {
        'Content-Type': 'application/yang-data+json',
        'Accept': 'application/yang-data+json'
    }
    auth = HTTPBasicAuth(username=routerUsername, password=routerPassword)
    response = requests.get(url=url, headers=headers, auth=auth, verify=False)
    if response.status_code == 200:
        print(f'Getting the interface Tunnel{routerInterfaceIndex} state...')
        print(response.text)
    return response


def set_tunnel_interface_destination_ip_address(routerHost: str, routerPort: int, routerUsername: str,
                                                routerPassword: str,
                                                routerInterfaceIndex: str, ipAddress: str) -> str:
    url = (f'https://{routerHost}:{routerPort}/restconf/data/Cisco-IOS-XE-native:native/interface/'
           f'Tunnel={routerInterfaceIndex}/Cisco-IOS-XE-tunnel:tunnel/destination/ipaddress-or-host/')
    headers = {
        'Content-Type': 'application/yang-data+json',
        'Accept': 'application/yang-data+json'
    }
    auth = HTTPBasicAuth(username=routerUsername, password=routerPassword)
    data = {
        'ipaddress-or-host': ipAddress
    }
    response = requests.patch(url=url, headers=headers, auth=auth, verify=False, json=data)
    if response.status_code == 204:
        logging.debug(f'The interface Tunnel{routerInterfaceIndex} has been updated successfully.')
        send_notification(tgBotToken, tgChatID, text=f'The IP address for interface Tunnel{routerInterfaceIndex} has '
                                                     f'been updated successfully to {ipAddress}.')
        get_current_interface_state(routerHost, routerPort, routerUsername, routerPassword, routerInterfaceIndex)
    return response


def send_notification(tgBotToken: str, tgChatID: str, text: str):
    url = f'https://api.telegram.org/bot{tgBotToken}/sendMessage?chat_id={tgChatID}&text={text}'
    response = requests.get(url)
    if response.status_code == 200:
        return True
    else:
        return False


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
