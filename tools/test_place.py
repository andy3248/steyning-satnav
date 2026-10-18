"""Safety properties for automated placement; run python3 -m unittest discover -s tools."""
import copy,unittest
from geo import Road,ll,roadnorm,xy
from place import match_feature,place_all

class PlacementTests(unittest.TestCase):
 def row(self,label,p,quality='map'):
  return [1,'Test Road',label,*ll(p),quality]
 def uprn(self,ident,p):
  a,b=ll(p);return {'p':xy(a,b),'ids':[str(ident)],'lat':a,'lon':b}
 def test_anchored_numbers_are_distinct_ordered_and_map_immutable(self):
  before={'annington':[self.row('1',(0,10)),self.row('3',(80,-20),'approx'),self.row('5',(40,10)),self.row('2',(0,-10)),self.row('4',(70,30),'guess'),self.row('6',(40,-10))],'ashurst':[],'wiston':[]}
  saved=copy.deepcopy(before);points=[self.uprn(100,(20,10)),self.uprn(101,(20,-10))]
  after,audit,models,roads=place_all(before,[],{roadnorm('Test Road'):[[(-50,0),(100,0)]]},points)
  self.assertEqual(before,saved)
  for i in [0,2,3,5]:self.assertEqual(after['annington'][i],before['annington'][i])
  self.assertEqual(after['annington'][1][3:6],[*ll((20,10)),'uprn'])
  self.assertEqual(after['annington'][4][3:6],[*ll((20,-10)),'uprn'])
  self.assertEqual([r[:3] for r in after['annington']],[r[:3] for r in before['annington']])
  self.assertEqual(len({tuple(r[3:5]) for r in after['annington']}),6)
 def test_numbering_without_anchors_stays_guess(self):
  before={'annington':[self.row('1',(5,-10),'approx'),self.row('2',(25,10),'approx')],'ashurst':[],'wiston':[]}
  points=[self.uprn(100,(20,10)),self.uprn(101,(20,-10))]
  after,*_=place_all(before,[],{roadnorm('Test Road'):[[(-50,0),(100,0)]]},points)
  self.assertTrue(all(r[5]=='guess' for r in after['annington']))
 def test_number_fallback_cannot_promote_wrong_side_point(self):
  before={'annington':[self.row('1',(0,10)),self.row('3',(20,10),'approx'),self.row('5',(40,10))],'ashurst':[],'wiston':[]}
  after,*_=place_all(before,[],{roadnorm('Test Road'):[[(-50,0),(100,0)]]},[self.uprn(100,(20,-10))])
  self.assertEqual(after['annington'][1][5],'guess')
 def test_preexisting_duplicates_get_distinct_unconfirmed_points(self):
  before={'annington':[self.row('East Cottage',(0,10),'guess'),self.row('West Cottage',(0,10),'guess')],'ashurst':[],'wiston':[]}
  points=[self.uprn(100,(0,10)),self.uprn(101,(15,10))]
  after,audit,*_=place_all(before,[],{roadnorm('Test Road'):[[(-50,0),(100,0)]]},points)
  self.assertEqual(len({tuple(r[3:5]) for r in after['annington']}),2)
  self.assertTrue(all(r[5]=='guess' for r in after['annington']))
  self.assertTrue(all(e['method']=='duplicate-unverified' for e in audit['annington']))
 def test_same_name_on_another_street_is_not_confirmed(self):
  model=Road('Test Road',[[(-50,0),(100,0)]],(0,0));row=self.row('Rose Cottage',(0,10),'approx')
  f={'id':'node/1','p':(0,10),'tags':{'name':'Rose Cottage','addr:street':'Different Road'}}
  self.assertIsNone(match_feature(row,model,[f]))
 def test_unlabelled_remote_same_name_is_not_confirmed(self):
  model=Road('Test Road',[[(-50,0),(100,0)]],(0,0));row=self.row('Rose Cottage',(0,10),'approx')
  f={'id':'node/1','p':(0,350),'tags':{'name':'Rose Cottage'}}
  self.assertIsNone(match_feature(row,model,[f]))
 def test_full_subaddress_matches_without_changing_frame_text(self):
  model=Road('Test Road',[[(-50,0),(100,0)]],(0,0));row=self.row('1 Iris Cottages',(0,10),'approx')
  f={'id':'node/1','p':(0,10),'tags':{'addr:housenumber':'1','addr:street':'Iris Cottages'}}
  self.assertEqual(match_feature(row,model,[f]),f)
 def test_cottage_unit_and_singular_group_name_match(self):
  model=Road('Test Road',[[(-50,0),(100,0)]],(0,0));row=self.row('1 Wheelers Common Cottage',(0,10),'approx')
  f={'id':'way/1','p':(0,10),'tags':{'addr:unit':'1','addr:housename':'Wheelers Common Cottages','addr:street':'Test Road'}}
  self.assertEqual(match_feature(row,model,[f]),f)
  f['tags']['addr:unit']='2';self.assertIsNone(match_feature(row,model,[f]))
 def test_cottage_sibling_uses_local_group_not_distant_frame_neighbour(self):
  before={'annington':[self.row('1 Test Cottages',(0,10)),self.row('2 Test Cottages',(15,10),'approx'),self.row('Distant Farm',(2000,10))],'ashurst':[],'wiston':[]}
  after,audit,*_=place_all(before,[],{roadnorm('Test Road'):[[(-50,0),(2100,0)]]},[self.uprn(100,(20,10)),self.uprn(101,(1000,10))])
  self.assertEqual(after['annington'][1][3:5],ll((20,10)))
  self.assertEqual(audit['annington'][1]['method'],'unit-neighbours')

if __name__=='__main__':unittest.main()
