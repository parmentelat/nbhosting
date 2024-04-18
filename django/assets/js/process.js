
async function read_process_stream(command, elementId) {
    // console.log('read_process_stream', command, elementId)
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

    const addLine = (line, className) => {
        const newdiv = document.createElement('div')
        newdiv.innerText = line
        newdiv.classList.add(className)
        element.appendChild(newdiv)
    }
    while (true) {
        const { value, done } = await reader.read()
        if (done)
            break
        // decode bytes as text
        const chunk = decoder.decode(value, { stream: true })
        console.debug(`chunk: ${chunk.length} long`, chunk)
        for (const line of chunk.split("\n")) {
            if (!line)
                continue
            try {
                const data = JSON.parse(line)
                // console.log('.')
                if ((data.type === 'stdout') || (data.type === 'stderr')) {
                    addLine(data.text, data.type)
                } else {
                    const retcod = data.retcod
                    const message = (retcod === 0) ? "Success (retcod=0)" : `Failed with retcode=${retcod}`
                    addLine(message, "retcod")
                    const classname = (retcod === 0) ? 'success' : 'failure'
                    element.classList.add(classname)
                }
            } catch (e) {
                console.log("error while decoding json:", "error=", e)
                addLine(`probably truncated json line ${line}`, "non-json")
            }
        }
    }
    console.log('done')
    if (!element.classList.contains('failure') && !element.classList.contains('success')) {
        element.classList.add('unknown')
    }
}
