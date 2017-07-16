# http_chat_server

A simple chat server written in Python3 utilizing curio and h11.

# Usage (as a client)

To utilize this server as a client, you must use something that lets you keep
cookies and do GET/POST/PUT/DELETE requests.

For this guide, we presume that:  
    1. You have imported [requests](https://github.com/kennethreitz/requests)  
    2. `s = requests.Session()`  
    3. You have a variable named `URL` that is assigned to the URL of the
       server.  

All other uppercased variables in the examples are to be replaced with your
values.

## Getting the latest messages and the current users on the server.

```python
s.get(URL, json={"username": USERNAME}).json()
```

## Sending a message

```python
s.post(URL, json={"username": USERNAME, "message": MESSAGE}).json()
```

## Logging off the server.

*N.B.*: You automatically log-in on the first action you send to the server.

```python
s.delete(URL; json={"username": USERNAME})
```
