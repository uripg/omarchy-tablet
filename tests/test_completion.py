import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/'backend'))
from completion import Completion
class CompletionTests(unittest.TestCase):
 def setUp(self): self.c=Completion(Path(__file__).parents[1]/'data'); self.c.set_focus('a')
 def test_ranked_completion_appends_only(self):
  self.c.feed('he'); self.assertEqual(self.c.suggestions(),['her','here','help']); self.assertEqual(self.c.suffix('help'),'lp '); self.assertEqual(self.c.prefix,'')
 def test_focus_change_cancels(self):
  self.c.feed('hello'); self.c.set_focus('b'); self.assertEqual(self.c.suggestions(),[])
 def test_navigation_and_deletion_cancel(self):
  for key in ('\x1b','\b','\t','\n',' '):
   self.c.feed('hel'+key); self.assertEqual(self.c.prefix,'')
 def test_stale_suggestion_rejected(self):
  self.c.feed('he')
  with self.assertRaises(ValueError): self.c.suffix('world')
 def test_case_and_spanish(self):
  self.c.feed('He');self.assertEqual(self.c.suggestions()[0],'Her')
  self.c.reset(); self.c.language='es'; self.c.feed('gra');self.assertIn('gracias',self.c.suggestions())
 def test_disabled_does_not_track(self):
  self.c.enabled=False;self.c.feed('anything');self.assertEqual(self.c.prefix,'')
if __name__=='__main__':unittest.main()
