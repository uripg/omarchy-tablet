#!/usr/bin/python3
"""Omarchy Tablet Mode controller. Spawned and stopped by the native plugin."""
import codecs, fcntl, glob, json, os, pathlib, signal, socket, subprocess, sys, time
from selectors import DefaultSelector, EVENT_READ
HOME = pathlib.Path.home()
ROOT = pathlib.Path(__file__).resolve().parents[1]
DATA = ROOT / 'data'
CONFIG = pathlib.Path(os.environ.get('XDG_CONFIG_HOME', HOME / '.config')) / 'omarchy-tablet'
APPDATA = pathlib.Path(os.environ.get('XDG_DATA_HOME', HOME / '.local/share')) / 'omarchy-tablet'
RUNTIME = pathlib.Path(os.environ['XDG_RUNTIME_DIR']) / 'omarchy-tablet'
SOCKET = RUNTIME / 'control.sock'
from completion import Completion
from reading import Reading
from hardware import load_settings, switch_state, choose_monitor, choose_devices, choose_backlight
SETTINGS = load_settings(CONFIG / 'settings.json')
PROMPTS = {
    'explain': 'Explain this clearly, with an example: ',
    'fix': 'Help me fix this. Identify the cause and propose a solution: ',
    'review': 'Review this for bugs, edge cases, and improvements: ',
    'rewrite': 'Rewrite this to be clear and concise, preserving my meaning: ',
    'plan': 'Create a practical step-by-step plan for: ',
    'continue': 'Continue from where you left off. ',
}


def run(*args):
    return subprocess.run(args, text=True, capture_output=True, timeout=5)

def sensor():
    return switch_state(SETTINGS['switch_name'])

def daemon():
    CONFIG.mkdir(parents=True, exist_ok=True)
    RUNTIME.mkdir(mode=0o700, exist_ok=True)
    lock = open(RUNTIME / 'lock', 'w')
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    SOCKET.unlink(missing_ok=True)
    server = socket.socket(socket.AF_UNIX)
    server.bind(str(SOCKET)); server.listen(8); server.setblocking(False)
    selector = DefaultSelector()
    selector.register(server, EVENT_READ)
    completion = Completion(DATA)
    reading = Reading(HOME, RUNTIME, run, preferences=CONFIG/'reading.json', shader_dir=ROOT/'ui/shaders')
    keyboard_before_zen = False
    decoder = codecs.getincrementaldecoder("utf-8")()
    keyboard_visible = False
    next_focus_check = 0
    next_sensor_check = 0
    next_publish = 0
    last_published = None
    system_values = {}
    system_checked = 0
    keyboard = None
    active = False
    physical = None
    override = None
    error = None
    monitor = choose_monitor(json.loads(run('hyprctl','monitors','-j').stdout),SETTINGS['monitor'])
    if monitor is None:raise RuntimeError('Configured display is not connected')
    output = monitor['name']
    initial_rotation = monitor['transform']
    rotation = initial_rotation
    device_info=json.loads(run('hyprctl','devices','-j').stdout)
    touches=choose_devices(device_info,'touch',SETTINGS['touch_devices'])
    pens=choose_devices(device_info,'tablets',SETTINGS['pen_devices'])
    backlight=choose_backlight(SETTINGS['backlight'])
    keyboard_path=APPDATA/'bin/wvkbd-tablet'
    setup_error='' if keyboard_path.exists() else 'Keyboard not built. Run scripts/setup in the plugin directory.'
    def rotate(value):
        nonlocal rotation
        if value not in (0,1,2,3):raise ValueError('Invalid rotation')
        monitor=choose_monitor(json.loads(run('hyprctl','monitors','-j').stdout),output)
        if monitor is None:raise ValueError('Tablet display is disconnected')
        mode=f"{monitor['width']}x{monitor['height']}@{monitor['refreshRate']}"
        position=f"{monitor['x']}x{monitor['y']}"
        quote=lambda text:json.dumps(text,ensure_ascii=False)
        lua=f'hl.monitor({{output={quote(output)}, mode={quote(mode)}, position={quote(position)}, scale={monitor["scale"]}, transform={value}}}); '
        for device in touches+pens:
            lua+=f'hl.device({{name={quote(device)}, output={quote(output)}, transform={value}}}); '
        result=run('hyprctl','repl',lua)
        if result.returncode or 'error' in result.stdout.lower():raise ValueError('Rotation failed')
        rotation=value
    def set_zen(value):
        nonlocal keyboard_visible, keyboard_before_zen
        if value == reading.active:return
        if value:
            keyboard_before_zen = keyboard_visible
            reading.enter()
            if keyboard and keyboard.poll() is None:
                keyboard.send_signal(signal.SIGUSR1)
            keyboard_visible = False
            completion.reset()
        else:
            reading.leave()
            if keyboard_before_zen and keyboard and keyboard.poll() is None:
                keyboard.send_signal(signal.SIGUSR2)
                keyboard_visible = True
    def set_active(value):
        nonlocal active, keyboard, keyboard_visible, decoder
        if not value and reading.active: set_zen(False)
        if value and keyboard_path.exists() and (keyboard is None or keyboard.poll() is not None):
            if keyboard is not None:
                try: selector.unregister(keyboard.stdout)
                except KeyError: pass
                keyboard.stdout.close()
                completion.reset()
            keyboard = subprocess.Popen([str(keyboard_path), '-H', str(SETTINGS['keyboard_height']), '-L', str(SETTINGS['keyboard_height']), '--fn', 'sans '+str(SETTINGS['keyboard_font_size']), '-l', 'simple,special,nav,emoji', '--landscape-layers', 'simple,special,nav,emoji', '-R', '10', '--bg', '11131b', '--fg', '242733', '--fg-sp', '34394b', '--press', '506689', '--text', 'cdd6f4', '--text-sp', 'cdd6f4', '--corner-radius', '16', '-o'] + (['--hidden'] if reading.active else []), stdout=subprocess.PIPE)
            os.set_blocking(keyboard.stdout.fileno(), False)
            selector.register(keyboard.stdout, EVENT_READ)
            decoder = codecs.getincrementaldecoder('utf-8')()
            keyboard_visible = not reading.active
        elif not value and keyboard is not None:
            if keyboard.poll() is None:
                keyboard.terminate(); keyboard.wait(timeout=3)
            try: selector.unregister(keyboard.stdout)
            except KeyError: pass
            keyboard.stdout.close()
            keyboard = None
            keyboard_visible = False
            completion.reset()
        if active != value:
            print('Tablet mode ' + ('on' if value else 'off'), flush=True)
        active = value
        if not value and rotation != initial_rotation: rotate(initial_rotation)
    def status():
        nonlocal system_checked, system_values
        if time.monotonic()-system_checked > .75 or not system_values:
            volume = run('wpctl','get-volume','@DEFAULT_AUDIO_SINK@').stdout.split()
            try:
                brightness=round(100*int((backlight/'brightness').read_text())/int((backlight/'max_brightness').read_text())) if backlight else None
            except OSError:brightness=None
            system_values={'brightness':brightness,'volume':round(float(volume[1])*100) if len(volume)>1 else 0,'muted':'[MUTED]' in volume}
            system_checked=time.monotonic()
        return dict(active=active, sensor=physical, override=override, error=(setup_error if not keyboard_path.exists() else "") or error,
                    keyboard=keyboard is not None and keyboard.poll() is None,
                    brightness=system_values['brightness'], volume=system_values['volume'],
                    muted=system_values['muted'], keyboard_visible=keyboard_visible,
                    suggestions=completion.suggestions(), words=completion.enabled, language=completion.language, rotation=rotation, zen=reading.active, gray=reading.gray, warm=reading.warm, monitor=output, backlight=backlight.name if backlight else '', keyboard_height=SETTINGS['keyboard_height'], media_player=SETTINGS['media_player'])
    def stop(*args):
        raise KeyboardInterrupt
    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)
    try:
        while True:
            if time.monotonic() >= next_sensor_check:
                try:
                    current = sensor()
                    error = None
                    if current != physical:
                        physical = current
                        override = None
                        print('Hardware switch: ' + str(current), flush=True)
                except (OSError, RuntimeError) as e:
                    error = str(e)
                next_sensor_check = time.monotonic()+.5
            set_active(override if override is not None else bool(physical))
            if active and time.monotonic() >= next_focus_check:
                completion.set_focus(json.loads(run('hyprctl','activewindow','-j').stdout or '{}').get('address'))
                next_focus_check = time.monotonic() + .3
            if time.monotonic() >= next_publish:
                payload=json.dumps(status())
                if payload!=last_published:
                    temp=RUNTIME/'status.json.new'
                    temp.write_text(payload);temp.chmod(0o600)
                    temp.replace(RUNTIME/'status.json')
                    last_published=payload
                next_publish=time.monotonic()+(.1 if active else 1)
            ready = selector.select(.1)
            for key, _ in ready:
                if key.fileobj is not server:
                    chunk = os.read(key.fd, 4096)
                    if chunk: completion.feed(decoder.decode(chunk))
                    else: selector.unregister(key.fileobj)
            if not any(key.fileobj is server for key, _ in ready):
                continue
            conn, _ = server.accept()
            with conn:
                conn.settimeout(2)
                try:
                    command = conn.recv(256).decode().strip()
                    if command in ('on', 'off', 'toggle', 'auto'):
                        override = {'on': True, 'off': False, 'toggle': not active, 'auto': None}[command]
                        set_active(override if override is not None else bool(physical))
                    elif command in ('zen','zen-on','zen-off'):
                        if not active: raise ValueError('Enable tablet mode first')
                        set_zen({'zen':not reading.active,'zen-on':True,'zen-off':False}[command])
                    elif command == 'quit':
                        conn.sendall(b'{}')
                        return
                    elif command in ('reading-gray','reading-warm'):
                        reading.toggle_filter(command.split('-')[1])
                    elif command == 'keyboard' and active and keyboard and keyboard.poll() is None:
                        if reading.active: set_zen(False)
                        keyboard.send_signal(signal.SIGRTMIN)
                        keyboard_visible = not keyboard_visible
                        completion.reset()
                    elif command in ('rotate','portrait','portrait-right','landscape'):
                        value = {'rotate': {0:1,1:3,2:0,3:0}[rotation], 'portrait':1, 'portrait-right':3, 'landscape':0}[command]
                        rotate(value)
                    elif command == 'words':
                        completion.enabled = not completion.enabled
                        completion.reset()
                    elif command == 'language':
                        completion.language = 'es' if completion.language == 'en' else 'en'
                        completion.reset()
                    elif command.startswith('complete:') or command.startswith('prompt:'):
                        focus = json.loads(run('hyprctl','activewindow','-j').stdout or '{}').get('address')
                        if not active or not keyboard_visible or not focus:
                            raise ValueError('No focused application')
                        completion.set_focus(focus)
                        if command.startswith('complete:'):
                            value = completion.suffix(command.split(':',1)[1])
                        else:
                            value = PROMPTS[command.split(':',1)[1]]
                            completion.reset()
                        # The argument is passed directly, never through a shell.
                        result = run('wtype', '--', value)
                        if result.returncode: raise ValueError('Text insertion failed')
                    elif command != 'status':
                        raise ValueError('Use on, off, toggle, auto, keyboard, or status')
                    conn.sendall(json.dumps(status()).encode())
                except (OSError, ValueError, KeyError, RuntimeError, subprocess.SubprocessError) as e:
                    print(str(e), flush=True)
    finally:
        if reading.active or reading.original is not None:
            try: reading.leave()
            except Exception as e: print('Reading restoration deferred: '+str(e), flush=True)
        if rotation != initial_rotation:
            try: rotate(initial_rotation)
            except Exception: pass
        for child in (keyboard,):
            if child and child.poll() is None:
                child.terminate()
        SOCKET.unlink(missing_ok=True)
        (RUNTIME/'status.json').unlink(missing_ok=True)

if __name__ == '__main__':
    if len(sys.argv) == 2 and sys.argv[1] == 'daemon':
        try: daemon()
        except KeyboardInterrupt: pass
    else:
        client = socket.socket(socket.AF_UNIX); client.settimeout(5)
        try:
            client.connect(str(SOCKET))
            client.sendall((sys.argv[1] if len(sys.argv)>1 else 'status').encode())
            response = client.recv(4096).decode()
            if len(sys.argv)<2 or sys.argv[1]=='status': print(response)
        except OSError as e:
            sys.exit('Tablet service unavailable: ' + str(e))
