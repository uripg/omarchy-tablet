"""Reversible reading filters and desktop-bar visibility."""
import json
from pathlib import Path

class Reading:
    def __init__(self, home, runtime, run, preferences=None, shader_dir=None):
        self.home=Path(home); self.run=run
        self.recovery=Path(runtime)/'reading-restore.json'
        self.preferences=Path(preferences) if preferences else self.home/'.config/omarchy-tablet/reading.json'
        self.shader_dir=Path(shader_dir) if shader_dir else Path(__file__).resolve().parents[1]/'ui/shaders'
        self.active=False; self.original=None
        self.gray=True; self.warm=True
        if self.preferences.exists():
            settings=json.loads(self.preferences.read_text())
            self.gray=bool(settings.get('gray',True)); self.warm=bool(settings.get('warm',True))
        if self.recovery.exists():
            self.original=json.loads(self.recovery.read_text())
            self.leave()
    def shader(self,path):
        # JSON string syntax is also valid for these simple Lua path strings.
        result=self.run('hyprctl','repl','hl.config({decoration={screen_shader='+json.dumps(path)+'}})')
        if result.returncode or 'error' in result.stdout.lower():
            raise RuntimeError('Could not set reading filter')
    def bar(self,hidden):
        # Omarchy's bar command controls the bar-off flag: on means hidden.
        result=self.run('omarchy','toggle','bar','on' if hidden else 'off')
        if result.returncode: raise RuntimeError('Could not change bar visibility')
    def apply(self):
        if self.gray or self.warm:
            self.shader(str(self.shader_dir/f'reading-{int(self.gray)}-{int(self.warm)}.frag'))
        else:
            self.shader(self.original['shader'])
    def enter(self):
        if self.active:return
        shader=json.loads(self.run('hyprctl','getoption','decoration:screen_shader','-j').stdout)['str']
        self.original={'shader':shader, 'bar_hidden':(self.home/'.local/state/omarchy/toggles/bar-off').exists()}
        # Record the restoration data before changing external desktop state.
        self.recovery.write_text(json.dumps(self.original)); self.recovery.chmod(0o600)
        try:
            self.apply(); self.bar(True)
            self.run('omarchy-menu','close')
            self.active=True
        except Exception:
            self.leave(); raise
    def leave(self):
        if self.original is not None:
            self.shader(self.original['shader'])
            self.bar(self.original['bar_hidden'])
            self.recovery.unlink(missing_ok=True)
        self.original=None; self.active=False
    def toggle_filter(self,which):
        if which=='gray':self.gray=not self.gray
        elif which=='warm':self.warm=not self.warm
        else:raise ValueError('Unknown reading filter')
        self.preferences.write_text(json.dumps({'gray':self.gray,'warm':self.warm})+'\n')
        if self.active:self.apply()
