import json,sys,tempfile,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/'backend'))
from hardware import load_settings,switch_devices,choose_monitor,choose_devices,choose_backlight

class HardwareTests(unittest.TestCase):
    def test_defaults_and_invalid_settings(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'settings.json'
            self.assertEqual(load_settings(path)['monitor'],'auto')
            for settings in ({'unknown':True},{'keyboard_height':True},{'keyboard_height':100},{'touch_devices':'random'},[]):
                path.write_text(json.dumps(settings))
                with self.assertRaises(ValueError):load_settings(path)
            path.write_text(json.dumps({'touch_devices':['touch'], 'keyboard_height':480}))
            self.assertEqual(load_settings(path)['touch_devices'],['touch'])
    def test_only_tablet_switch_is_detected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            for event,bits in [('event0','1'),('event1','2'),('event2','3'),('event3','invalid')]:
                device=root/event/'device';(device/'capabilities').mkdir(parents=True)
                (device/'name').write_text(event);(device/'capabilities/sw').write_text(bits)
            self.assertEqual(switch_devices(root),[('event1','event1'),('event2','event2')])
    def test_internal_panel_and_explicit_selection(self):
        monitors=[{'name':'HDMI-A-1','focused':True},{'name':'eDP-1'}]
        self.assertEqual(choose_monitor(monitors)['name'],'eDP-1')
        self.assertEqual(choose_monitor(monitors,'HDMI-A-1')['name'],'HDMI-A-1')
        self.assertIsNone(choose_monitor(monitors,'missing'))
        self.assertIsNone(choose_monitor([]))
    def test_ambiguous_touchscreens_are_not_guessed(self):
        self.assertEqual(choose_devices({'touch':[{'name':'a'}]},'touch','auto'),['a'])
        devices={'touch':[{'name':'a'},{'name':'b'}]}
        self.assertEqual(choose_devices(devices,'touch','auto'),[])
        self.assertEqual(choose_devices(devices,'touch',['b']),['b'])
    def test_missing_backlight(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertIsNone(choose_backlight(root=Path(tmp)))
            (Path(tmp)/'panel').mkdir()
            self.assertEqual(choose_backlight(root=Path(tmp)).name,'panel')
            self.assertIsNone(choose_backlight('missing',Path(tmp)))
