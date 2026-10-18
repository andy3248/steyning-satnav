"""Build a single-file, offline map comparing immutable baseline and new pins."""
import json

def write_review(root,report,before,after):
 payload={r:{'map':(root/'src'/r/'basemap.txt').read_text(),'entries':report['rounds'][r]['entries'],'before':report['rounds'][r]['before'],'after':report['rounds'][r]['after'],'checks':report['rounds'][r]['road_checks']} for r in before}
 source=(root/'tools/pin-review-template.html').read_text()
 (root/'docs/pin-review.html').write_text(source.replace('/*REVIEW_DATA*/',json.dumps(payload,ensure_ascii=False,separators=(',',':')).replace('</','<\\/')))
