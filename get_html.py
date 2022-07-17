from typing import Optional


def get_html(port: Optional[str] = None) -> str:
    name_port = ''
    if port is None:
        port = ''
    else:
        name_port = f'({port})'
        port = '/' + port
    return """
<!DOCTYPE html>
<html>
    <head>
        <title>Robot ("""+name_port+""")</title>
    </head>
    <body>
        <h1>WebSocket Robot """+name_port+"""</h1>
        <form action="" onsubmit="sendMessage(event)">
            <input type="text" id="messageText" autocomplete="off"/>
            <button>Send</button>
        </form>
        <ul id='messages'>
        </ul>
        <script>
            var ws = new WebSocket("ws://"+window.location.host+"/ws"""+port+"""");
            ws.onmessage = function(event) {
                var messages = document.getElementById('messages')
                var message = document.createElement('li')
                var content = document.createTextNode(event.data)
                message.appendChild(content)
                messages.appendChild(message)
            };
            function sendMessage(event) {
                var input = document.getElementById("messageText")
                ws.send(input.value)
                input.value = ''
                event.preventDefault()
            }
        </script>
    </body>
</html>
"""