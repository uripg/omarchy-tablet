"""Memory-only completion for text emitted by the tablet keyboard."""
import json
from pathlib import Path

class Completion:
    def __init__(self, directory):
        self.words = {lang: json.loads((Path(directory)/f'words-{lang}.json').read_text()) for lang in ('en','es')}
        self.language = 'en'
        self.enabled = True
        self.prefix = ''
        self.focus = None
    def reset(self):
        self.prefix = ''
    def set_focus(self, address):
        if address != self.focus:
            self.reset()
            self.focus = address
    def feed(self, text):
        if not self.enabled:
            return
        for char in text:
            if char.isalpha():
                self.prefix = (self.prefix + char)[-64:]
            else:
                # Navigation, deletion, punctuation and shortcuts invalidate our
                # fragment. Never guess cursor position or erase application text.
                self.reset()
    def suggestions(self):
        if not self.enabled or len(self.prefix)<2:
            return []
        prefix = self.prefix.lower()
        result=[]
        for word in self.words[self.language]:
            if word.startswith(prefix) and len(word)>len(prefix):
                if self.prefix.isupper(): word=word.upper()
                elif self.prefix[0].isupper(): word=word.capitalize()
                result.append(word)
                if len(result)==3: break
        return result
    def suffix(self, word):
        if word not in self.suggestions():
            raise ValueError('Suggestion expired')
        suffix=word[len(self.prefix):]+' '
        self.reset()
        return suffix
