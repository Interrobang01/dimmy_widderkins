import requests
import json
import time
import sys
from typing import Union, Dict, Any

class BrookError(Exception):
    """Custom exception for Brook API errors"""
    pass

class Brook:
    """
    A Python client for interacting with the Brook bot's economy API.
    
    This class provides high-level methods that communicate with the TypeScript
    Brook server via HTTP requests, allowing Python code to use Brook functionality.
    """
    
    def __init__(self, server_url: str = "http://localhost:3000"):
        """
        Creates a new Brook API client instance.
        
        Args:
            server_url: The URL of the Brook TypeScript server
        """
        self.server_url = server_url.rstrip('/')
        self._session = requests.Session()
        self._session.headers.update({
            'Content-Type': 'application/json'
        })
    
    def _parse_response(self, response: requests.Response) -> Dict[str, Any]:
        """
        Parse response with better error handling.
        
        Args:
            response: The HTTP response object
            
        Returns:
            Parsed JSON data
            
        Raises:
            BrookError: If response cannot be parsed or contains errors
        """
        try:
            if response.headers.get('content-type', '').startswith('application/json'):
                return response.json()
            else:
                # Server returned non-JSON response
                raise BrookError(f"Server returned non-JSON response: {response.text[:200]}")
        except json.JSONDecodeError as e:
            raise BrookError(f"Failed to parse server response as JSON: {response.text[:200]}")
    
    def _wait_for_server(self, timeout: int = 30) -> bool:
        """
        Wait for the server to be available.
        
        Args:
            timeout: Maximum time to wait in seconds
            
        Returns:
            True if server is available, False if timeout reached
        """
        print(f"Waiting for Brook server at {self.server_url}...")
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                response = self._session.get(f"{self.server_url}/health", timeout=2)
                if response.ok:
                    print("Brook server is available!")
                    return True
            except requests.exceptions.RequestException:
                pass
            
            time.sleep(1)
        
        return False
    
    def initialize(self, token: str, transport_channel_id: str, wait_for_server: bool = True) -> None:
        """
        Initialize the Discord bot connection on the server.
        
        Args:
            token: Discord bot token
            transport_channel_id: ID of the channel for API transport
            wait_for_server: Whether to wait for the server to be available
        """
        if wait_for_server:
            if not self._wait_for_server():
                raise BrookError(
                    "Brook server is not available. Please start the TypeScript server first:\n"
                    "  cd /home/interrobang/Scripts/DimmyWidderkins\n"
                    "  npm install\n"
                    "  npx ts-node brook_server.ts"
                )
        
        try:
            response = self._session.post(f"{self.server_url}/init", json={
                "token": token,
                "transportChannelId": transport_channel_id
            })
            
            data = self._parse_response(response)
            if not data.get('success'):
                raise BrookError(f"Failed to initialize: {data.get('error', f'HTTP {response.status_code}')}")
                
        except requests.exceptions.ConnectionError:
            raise BrookError(
                "Could not connect to Brook server. Please ensure the TypeScript server is running:\n"
                "  cd /home/interrobang/Scripts/DimmyWidderkins\n"
                "  npx ts-node brook_server.ts"
            )
        except requests.exceptions.RequestException as e:
            raise BrookError(f"Request failed: {str(e)}")
    
    def request_payment(self, user_id: str, amount: float, request_channel_id: str, description: str) -> Dict[str, Any]:
        """
        Request a payment from a user.
        
        This sends an interactive message to the target user and waits for their response.
        It is a long-running operation that can take a long time to resolve.
        
        Args:
            user_id: The ID of the user you are requesting payment from
            amount: The amount of money to request
            request_channel_id: The ID of the channel where the interactive payment request message should be sent
            description: A string explaining the reason for the payment request
            
        Returns:
            Payment information if accepted
            
        Raises:
            BrookError: If the payment request fails
        """
        try:
            print(f"Requesting payment from user {user_id} for amount {amount} in channel {request_channel_id} with description '{description}'")
            response = self._session.post(f"{self.server_url}/request-payment", json={
                "userId": user_id,
                "amount": amount,
                "requestChannelId": request_channel_id,
                "description": description
            })
            
            # Debug: print response details
            print(f"Response status: {response.status_code}")
            print(f"Response headers: {dict(response.headers)}")
            print(f"Response text: {response.text[:500]}")
            
            data = self._parse_response(response)
            if not data.get('success'):
                raise BrookError(f"Payment request failed: {data.get('error', 'Unknown error')}")
            
            return data
            
        except requests.exceptions.RequestException as e:
            raise BrookError(f"Request failed: {str(e)}")
    
    def pay(self, target: str, amount: float) -> Dict[str, Any]:
        """
        Pay a user or an organization.
        
        This immediately transfers funds from the client's account to the target.
        
        Args:
            target: A string ID representing the recipient (can be a user or an organization)
            amount: The amount of money to pay
            
        Returns:
            Payment details
            
        Raises:
            BrookError: If the payment fails
        """
        try:
            response = self._session.post(f"{self.server_url}/pay", json={
                "target": target,
                "amount": amount
            })
            
            data = self._parse_response(response)
            if not data.get('success'):
                raise BrookError(f"Payment failed: {data.get('error', 'Unknown error')}")
            
            return data
            
        except requests.exceptions.RequestException as e:
            raise BrookError(f"Request failed: {str(e)}")
    
    def balance(self, target: str) -> float:
        """
        Get the current balance of a user or organization.
        
        Args:
            target: A string ID representing the account to check
            
        Returns:
            The account balance
            
        Raises:
            BrookError: If the balance check fails
        """
        try:
            response = self._session.get(f"{self.server_url}/balance/{target}")
            
            data = self._parse_response(response)
            if not data.get('success'):
                raise BrookError(f"Balance check failed: {data.get('error', 'Unknown error')}")
            
            return data
            
        except requests.exceptions.RequestException as e:
            raise BrookError(f"Request failed: {str(e)}")
