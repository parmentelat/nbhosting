from subprocess import Popen, PIPE
import selectors
import json

from django.http import StreamingHttpResponse, HttpResponseNotFound
from django.contrib.admin.views.decorators import staff_member_required
from django.views.decorators.csrf import csrf_protect

@staff_member_required
@csrf_protect
def run_process_and_stream_output(request):
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
    if request.method != 'POST':
        return HttpResponseNotFound()
    data = json.loads(request.body.decode())
    command = data['command']
    print(f" in run_process_and_stream_output: command={command}")
    def stream_output():
        with Popen(command, stdout=PIPE, stderr=PIPE) as process:
            sel = selectors.DefaultSelector()
            sel.register(process.stdout, selectors.EVENT_READ)
            sel.register(process.stderr, selectors.EVENT_READ)

            while True:
                for key, _ in sel.select():
                    data = key.fileobj.read1().decode()
                    if not data:
                        sel.unregister(process.stdout)
                        sel.unregister(process.stderr)
                        process.wait()
                        yield json.dumps({'type': 'returncode', 'retcod': process.returncode}) + "\n"
                        return
                    if key.fileobj is process.stdout:
                        yield json.dumps({'type': 'stdout', 'text': data}) + "\n"
                    else:
                        yield json.dumps({'type': 'stderr', 'text': data}) + "\n"

    return StreamingHttpResponse(stream_output())
