from subprocess import Popen, PIPE
import selectors
import json

from django.http import StreamingHttpResponse, HttpResponseNotFound
from django.contrib.admin.views.decorators import staff_member_required
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_POST

# to split the output of a command into lines
class LineBuffer:
    def __init__(self, name):
        self.name = name
        self.content = ''
    def append(self, char):
        if char == '\n':
            line, self.content = self.content, ''
            return line
        self.content += char
        return None


@staff_member_required
@csrf_protect
@require_POST
def run_process_and_stream_outputs(request):
    """
    this view allows to trigger a command and stream its output
    Parameters:
      - command: the command to run, as a list of strings
    Returns:
      - a StreamingHttpResponse object that streams the output of the command
        each chunk is the JSON representation of a line of output with
          - type: stdout or stderr
          - line: the line of output
    this view is reachable from POST only and should be used with CSRF protection
    """
    post_body = json.loads(request.body.decode())
    command = post_body['command']
    print(f" in run_process_and_stream_outputs: command={command}")
    def stream_outputs():
        with Popen(command, stdout=PIPE, stderr=PIPE,
                   text=True, bufsize=8) as process:
            sel = selectors.DefaultSelector()
            sel.register(process.stdout, selectors.EVENT_READ)
            sel.register(process.stderr, selectors.EVENT_READ)
            buffers = {
                process.stdout: LineBuffer('stdout'),
                process.stderr: LineBuffer('stderr'),
            }

            # to know when to stop
            channels = 2
            while True:
                for key, _ in sel.select():
                    # read one character at a time
                    data = key.fileobj.read(1)
                    buffer = buffers[key.fileobj]
                    if not data:
                        # close the channel
                        sel.unregister(key.fileobj)
                        channels -= 1
                        # in case the process does not end with a newline
                        if buffer.content:
                            yield json.dumps({'type': buffer.name, 'line': buffer.content}) + "\n"
                    # end when both channels are closed
                    if not channels:
                        sel.close()
                        process.wait()
                        yield json.dumps({'type': 'returncode', 'retcod': process.returncode}) + "\n"
                        return
                    line = buffer.append(data)
                    if line:
                        yield json.dumps({'type': buffer.name, 'text': line}) + "\n"

    return StreamingHttpResponse(
        stream_outputs(),
        # this is to keep nginx from buffering
        # which altogether ruins the 'on the fly' side of things
        headers={
            'X-Accel-Buffering': 'no',
        }
    )
