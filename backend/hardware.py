"""Discover a convertible's switch, internal display, touchscreen and backlight."""
import fcntl,json
from pathlib import Path

DEFAULTS = {
    'monitor':'auto', 'switch_name':'auto', 'backlight':'auto',
    'touch_devices':'auto', 'pen_devices':'auto', 'keyboard_height':400,
    'keyboard_font_size':24, 'media_player':'brave',
}

def load_settings(path):
    settings=dict(DEFAULTS)
    if path.exists():
        overrides=json.loads(path.read_text())
        if not isinstance(overrides,dict): raise ValueError('settings.json must contain an object')
        unknown=set(overrides)-set(DEFAULTS)
        if unknown: raise ValueError('Unknown settings: '+', '.join(sorted(unknown)))
        settings.update(overrides)
    for key in ('monitor','switch_name','backlight','media_player'):
        if not isinstance(settings[key],str):raise ValueError(key+' must be a string')
    for key in ('touch_devices','pen_devices'):
        value=settings[key]
        if value!='auto' and not (isinstance(value,list) and all(isinstance(x,str) for x in value)):
            raise ValueError(key+' must be "auto" or a list of device names')
    for key,lo,hi in (('keyboard_height',240,600),('keyboard_font_size',14,32)):
        if type(settings[key]) is not int or not lo<=settings[key]<=hi:raise ValueError(f'{key} must be {lo}..{hi}')
    return settings

def switch_devices(root=Path('/sys/class/input')):
    found=[]
    for event in sorted(root.glob('event*')):
        try:
            bits=int((event/'device/capabilities/sw').read_text().strip().replace(' ',''),16)
            if bits & 2:found.append((event.name,(event/'device/name').read_text().strip()))
        except (OSError,ValueError):continue
    return found

def switch_state(name='auto'):
    matches=[(event,label) for event,label in switch_devices() if name=='auto' or name==label]
    if not matches:raise RuntimeError('No tablet switch detected. Use the bar button for manual mode.')
    values=[]
    for event,label in matches:
        try:
            with open('/dev/input/'+event,'rb',buffering=0) as device:
                bits=bytearray(8);fcntl.ioctl(device,0x8008451b,bits);values.append(bool(bits[0]&2))
        except PermissionError:
            raise RuntimeError('Tablet switch permission missing. Run scripts/setup-input, or use manual mode.') from None
    return any(values)

def choose_monitor(monitors,name='auto'):
    if name!='auto':
        return next((m for m in monitors if m['name']==name),None)
    internal=[m for m in monitors if m['name'].startswith(('eDP','LVDS','DSI'))]
    return next(iter(internal),next((m for m in monitors if m.get('focused')), next(iter(monitors),None)))

def choose_devices(devices,kind,setting):
    if setting!='auto':return setting
    names=[d['name'] for d in devices.get(kind,[]) if d.get('name')]
    # Do not guess which of several touchscreens belongs to the internal panel.
    return names if len(names)==1 else []

def choose_backlight(name='auto',root=Path('/sys/class/backlight')):
    devices=sorted(root.iterdir())
    if name!='auto':return next((d for d in devices if d.name==name),None)
    return next(iter(devices),None)
