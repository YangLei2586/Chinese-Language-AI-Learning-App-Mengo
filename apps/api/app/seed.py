from sqlalchemy.orm import Session
from .models import Scenario
SCENARIOS=[
{"id":"introductions","title":"First introductions","title_zh":"初次见面","category":"Everyday","level":"beginner","duration_minutes":5,"prompt":"Meet a new friend and introduce yourself with a friendly hello.","vocabulary":[{"hanzi":"你好","pinyin":"nǐ hǎo","english":"hello"},{"hanzi":"名字","pinyin":"míngzi","english":"name"}]},
{"id":"ordering-food","title":"Order a meal","title_zh":"点餐","category":"Food","level":"beginner","duration_minutes":8,"prompt":"Order a simple meal at a neighborhood restaurant.","vocabulary":[{"hanzi":"饺子","pinyin":"jiǎozi","english":"dumplings"},{"hanzi":"想","pinyin":"xiǎng","english":"would like"}]},
{"id":"travel","title":"Find the subway","title_zh":"找地铁","category":"Travel","level":"elementary","duration_minutes":8,"prompt":"Ask for directions to the subway station.","vocabulary":[{"hanzi":"地铁站","pinyin":"dìtiě zhàn","english":"subway station"},{"hanzi":"前面","pinyin":"qiánmiàn","english":"ahead"}]},
{"id":"work-meeting","title":"Join a work meeting","title_zh":"参加会议","category":"Work","level":"elementary","duration_minutes":10,"prompt":"Confirm a meeting time and share a short idea.","vocabulary":[{"hanzi":"会议","pinyin":"huìyì","english":"meeting"},{"hanzi":"想法","pinyin":"xiǎngfǎ","english":"idea"}]}]
def seed_scenarios(db:Session):
 for item in SCENARIOS:
  if not db.get(Scenario,item["id"]): db.add(Scenario(**item))
 db.commit()
