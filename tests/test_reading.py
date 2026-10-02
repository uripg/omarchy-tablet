import json,sys,tempfile,unittest
from pathlib import Path
from types import SimpleNamespace
sys.path.insert(0,str(Path(__file__).parents[1]/'backend'))
from reading import Reading
class ReadingTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.home=Path(self.tmp.name)
  (self.home/'.config/omarchy-tablet').mkdir(parents=True)
  self.calls=[]
  def run(*args):
   self.calls.append(args)
   return SimpleNamespace(returncode=0,stdout=json.dumps({'str':'/original.frag'}) if 'getoption' in args else 'ok')
  self.run=run
 def tearDown(self):self.tmp.cleanup()
 def test_enter_and_restore(self):
  r=Reading(self.home,self.home,self.run);r.enter()
  self.assertTrue(r.active);self.assertTrue(r.recovery.exists())
  self.assertIn('reading-1-1.frag',self.calls[1][-1])
  r.leave();self.assertFalse(r.active);self.assertFalse(r.recovery.exists())
  self.assertIn('/original.frag',self.calls[-2][-1]);self.assertEqual(self.calls[-1],('omarchy','toggle','bar','off'))
 def test_preserve_already_hidden_bar(self):
  flag=self.home/'.local/state/omarchy/toggles/bar-off';flag.parent.mkdir(parents=True);flag.touch()
  r=Reading(self.home,self.home,self.run);r.enter();r.leave()
  self.assertEqual(self.calls[-1][-1],'on')
 def test_filter_combinations_and_persistence(self):
  r=Reading(self.home,self.home,self.run);r.enter()
  r.toggle_filter('gray');self.assertIn('reading-0-1.frag',self.calls[-1][-1])
  r.toggle_filter('warm');self.assertIn('/original.frag',self.calls[-1][-1])
  r.toggle_filter('gray');self.assertIn('reading-1-0.frag',self.calls[-1][-1])
  r.leave();other=Reading(self.home,self.home,self.run)
  self.assertTrue(other.gray);self.assertFalse(other.warm)
 def test_crash_recovery(self):
  r=Reading(self.home,self.home,self.run);r.enter()
  recovered=Reading(self.home,self.home,self.run)
  self.assertFalse(recovered.active);self.assertFalse(recovered.recovery.exists())
  self.assertIn('/original.frag',self.calls[-2][-1])
if __name__=='__main__':unittest.main()
