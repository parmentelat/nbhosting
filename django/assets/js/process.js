
async function read_process_stream(command, elementId) {
    console.log('read_process_stream', command, elementId)
    const element = document.getElementById(elementId)
    const csrftoken = document.querySelector('[name=csrfmiddlewaretoken]').value
    const request = {
        method: 'POST',
        body: JSON.stringify({ command: command }),
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrftoken,
          },
    }
    const url = '/process/run'
    const response = await fetch(url, request)
    // streaming response
    const reader = response.body.getReader()
    const decoder = new TextDecoder()

    while (true) {
        const { value, done } = await reader.read()
        if (done)
            break
        try {
            // decode bytes as text
            const chunk = decoder.decode(value, { stream: true })
            // console.log('chunk:', chunk)
            for (const line of chunk.split("\n")) {
                if (! line)
                    continue
                const data = JSON.parse(line)
                // console.log('.')
                if ((data.type === 'stdout') || (data.type === 'stderr')) {
                    const newdiv = document.createElement('div')
                    newdiv.innerText = data.text
                    newdiv.classList.add(data.type)
                    element.appendChild(newdiv)
                } else {
                    const retcod = data.retcod
                    const newdiv = document.createElement('div')
                    newdiv.classList.add("retcod")
                    const message = (retcod === 0) ? "Success (retcod=0)" : `Failed with retcode=${retcod}`
                    newdiv.innerText = message
                    element.appendChild(newdiv)
                    const classname = (retcod === 0) ? 'success' : 'failure'
                    element.classList.add(classname)
                }
            }
        } catch (e) {
            console.log("error while decoding json:", "error=", e)
        }
    }
}
