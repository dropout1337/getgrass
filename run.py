import asyncio
import random
import ssl
import json
import time
import uuid
import base64
import aiohttp
from datetime import datetime
from colorama import init, Fore, Style
from websockets_proxy import Proxy, proxy_connect

init(autoreset=True)

BANNER = """
_________ ____________________                            
__  ____/______  /__  ____/____________ _______________
_  / __ _  _ \\  __/  / __ __  ___/  __ `/_  ___/_  ___/
/ /_/ / /  __/ /_ / /_/ / _  /   / /_/ /_(__  )_(__  ) 
\\____/  \\___/\\__/ \\____/  /_/    \\__,_/ /____/ /____/  
"""

EDGE_USERAGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36 Edg/122.0.2365.57",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36 Edg/122.0.2365.52",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36 Edg/122.0.2365.46",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36 Edg/121.0.2277.128",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36 Edg/121.0.2277.112",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36 Edg/121.0.2277.98",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36 Edg/121.0.2277.83",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.2210.133",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.2210.121",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.2210.91"
]

HTTP_STATUS_CODES = {
    200: "OK",
    201: "Created", 
    202: "Accepted",
    204: "No Content",
    400: "Bad Request",
    401: "Unauthorized",
    403: "Forbidden", 
    404: "Not Found",
    500: "Internal Server Error",
    502: "Bad Gateway",
    503: "Service Unavailable",
    504: "Gateway Timeout"
}

def colorful_log(proxy, device_id, message_type, message_content, is_sent=False, mode=None):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    color = Fore.GREEN if is_sent else Fore.BLUE
    action_color = Fore.YELLOW
    mode_color = Fore.LIGHTYELLOW_EX
    
    log_message = (
        f"{Fore.WHITE}[{timestamp}] "
        f"{Fore.MAGENTA}[Proxy: {proxy}] "
        f"{Fore.CYAN}[Device ID: {device_id}] "
        f"{action_color}[{message_type}] "
        f"{color}{message_content} "
        f"{mode_color}[{mode}]"
    )
    
    print(log_message)

async def connect_to_wss(socks5_proxy, user_id, mode):
    device_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, socks5_proxy))
    
    random_user_agent = random.choice(EDGE_USERAGENTS)
    
    colorful_log(
        proxy=socks5_proxy,  
        device_id=device_id, 
        message_type="INITIALIZATION", 
        message_content=f"User Agent: {random_user_agent}",
        mode=mode
    )

    has_received_action = False
    is_authenticated = False
    
    while True:
        try:
            await asyncio.sleep(random.randint(1, 10) / 10)
            custom_headers = {
                "User-Agent": random_user_agent,
                "Origin": "chrome-extension://lkbnfiajjmbhnfledhphioinpickokdi" if mode == "extension" else None
            }
            custom_headers = {k: v for k, v in custom_headers.items() if v is not None}
            
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            
            urilist = [
                #"wss://proxy.wynd.network:4444/",
                #"wss://proxy.wynd.network:4650/",
                "wss://proxy2.wynd.network:4444/",
                "wss://proxy2.wynd.network:4650/",
                #"wss://proxy3.wynd.network:4444/",
                #"wss://proxy3.wynd.network:4650/"
            ]
            uri = random.choice(urilist)
            server_hostname = "proxy.wynd.network"
            proxy = Proxy.from_url(socks5_proxy)
            
            async with proxy_connect(uri, proxy=proxy, ssl=ssl_context, server_hostname=server_hostname,
                                     extra_headers=custom_headers) as websocket:
                async def send_ping():
                    while True:
                        # if has_received_action:
                        send_message = json.dumps(
                            {"id": str(uuid.uuid5(uuid.NAMESPACE_DNS, socks5_proxy)), 
                                "version": "1.0.0", 
                                "action": "PING", 
                                "data": {}})
                        
                        colorful_log(
                            proxy=socks5_proxy,  
                            device_id=device_id, 
                            message_type="SENDING PING", 
                            message_content=send_message,
                            is_sent=True,
                            mode=mode
                        )
                        
                        await websocket.send(send_message)
                        await websocket.ping()
                        await asyncio.sleep(5)

                await asyncio.sleep(1)
                ping_task = asyncio.create_task(send_ping())

                while True:
                    if is_authenticated and not has_received_action:
                        colorful_log(
                            proxy=socks5_proxy,
                            device_id=device_id,
                            message_type="AUTHENTICATED | WAIT UNTIL THE PING GATE OPENS",
                            message_content="Waiting for " + ("HTTP_REQUEST" if mode == "extension" else "OPEN_TUNNEL"),
                            mode=mode
                        )
                    
                    response = await websocket.recv()
                    message = json.loads(response)
                    
                    colorful_log(
                        proxy=socks5_proxy, 
                        device_id=device_id, 
                        message_type="RECEIVED", 
                        message_content=json.dumps(message),
                        mode=mode
                    )

                    if message.get("action") == "AUTH":
                        auth_response = {
                            "id": message["id"],
                            "origin_action": "AUTH",
                            "result": {
                                "browser_id": device_id,
                                "user_id": user_id,
                                "user_agent": random_user_agent,
                                "timestamp": int(time.time()),
                                "device_type": "extension" if mode == "extension" else "desktop",
                                "version": "4.26.2" if mode == "extension" else "4.30.0"
                            }
                        }
                        
                        if mode == "extension":
                            auth_response["result"]["extension_id"] = "lkbnfiajjmbhnfledhphioinpickokdi"
                        
                        colorful_log(
                            proxy=socks5_proxy,  
                            device_id=device_id, 
                            message_type="AUTHENTICATING", 
                            message_content=json.dumps(auth_response),
                            is_sent=True,
                            mode=mode
                        )
                        
                        await websocket.send(json.dumps(auth_response))
                        is_authenticated = True
                    
                    elif message.get("action") in ["HTTP_REQUEST", "OPEN_TUNNEL"]:
                        has_received_action = True
                        request_data = message["data"]
                        
                        headers = {
                            "User-Agent": custom_headers["User-Agent"],
                            "Content-Type": "application/json; charset=utf-8"
                        }
                        
                        async with aiohttp.ClientSession() as session:
                            async with session.get(request_data["url"], headers=headers) as api_response:
                                content = await api_response.text()
                                encoded_body = base64.b64encode(content.encode()).decode()
                                
                                status_text = HTTP_STATUS_CODES.get(api_response.status, "")
                                
                                http_response = {
                                    "id": message["id"],
                                    "origin_action": message["action"],
                                    "result": {
                                        "url": request_data["url"],
                                        "status": api_response.status,
                                        "status_text": status_text,
                                        "headers": dict(api_response.headers),
                                        "body": encoded_body
                                    }
                                }
                                
                                colorful_log(
                                    proxy=socks5_proxy,
                                    device_id=device_id,
                                    message_type="OPENING PING ACCESS",
                                    message_content=json.dumps(http_response),
                                    is_sent=True,
                                    mode=mode
                                )
                                
                                await websocket.send(json.dumps(http_response))

                    elif message.get("action") == "PONG":
                        pong_response = {"id": message["id"], "origin_action": "PONG"}
                        
                        colorful_log(
                            proxy=socks5_proxy, 
                            device_id=device_id, 
                            message_type="SENDING PONG", 
                            message_content=json.dumps(pong_response),
                            is_sent=True,
                            mode=mode
                        )
                        
                        await websocket.send(json.dumps(pong_response))
                        
        except Exception as e:
            colorful_log(
                proxy=socks5_proxy, 
                device_id=device_id, 
                message_type="ERROR", 
                message_content=str(e),
                mode=mode
            )
            await asyncio.sleep(5)

async def main():
    print(f"{Fore.CYAN}{BANNER}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}IM-Hanzou | GetGrass Crooter V2{Style.RESET_ALL}")
    
    print(f"{Fore.GREEN}Select Mode:{Style.RESET_ALL}")
    print("1. Extension Mode")
    print("2. Desktop Mode")
    
    while True:
        mode_choice = input("Enter your choice (1/2): ").strip()
        if mode_choice in ['1', '2']:
            break
        print(f"{Fore.RED}Invalid choice. Please enter 1 or 2.{Style.RESET_ALL}")
    
    mode = "extension" if mode_choice == "1" else "desktop"
    print(f"{Fore.GREEN}Selected mode: {mode}{Style.RESET_ALL}")
    
    _user_id = input('Please Enter your user ID: ')
    
    with open('proxy_list.txt', 'r') as file:
        local_proxies = file.read().splitlines()
    
    print(f"{Fore.YELLOW}Total Proxies: {len(local_proxies)}{Style.RESET_ALL}")
    
    tasks = [asyncio.ensure_future(connect_to_wss(i, _user_id, mode)) for i in local_proxies]
    await asyncio.gather(*tasks)

if __name__ == '__main__':
    asyncio.run(main())
