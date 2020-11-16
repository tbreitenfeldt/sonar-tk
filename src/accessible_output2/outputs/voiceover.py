import subprocess
import os

from .base import Output

class VoiceOver(Output):
    """Speech output supporting the Apple VoiceOver screen reader."""

    def runAppleScript(self, command, process = 'voiceover'):
        return subprocess.Popen(['osascript', '-e', 'tell application "' + process + '"\n' + command + '\nend tell'], stdout = subprocess.PIPE).communicate()[0]

    def speak(self, text, interrupt=0):
        if interrupt:
            self.silence()

        os.system('osascript -e \"tell application \\\"voiceover\\\" to output \\\"%s\\\"\" &' % text)

    def silence (self):
        self.runAppleScript('output ""')

    def is_active(self):
        return self.runAppleScript('return (name of processes) contains "VoiceOver"', 'system events').startswith(b'true') and not self.runAppleScript('try\nreturn bounds of vo cursor\non error\n'
        'return false\nend try').startswith(b'false')

output_class = VoiceOver