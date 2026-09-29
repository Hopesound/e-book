from pathlib import Path
import json
p=Path('manuscript/reviewed-pages.json')
a=json.loads(p.read_text(encoding='utf-8-sig'))
a[2]['ko'][-1]=a[2]['ko'][-1].replace('해당 지…','해당 지번…')
a[3]['ko'][0]=a[3]['ko'][0].replace('[3쪽에서 계속] …번 안에','[3쪽에서 계속] 해당 지번 안에')
a[6]['ja']=a[6]['ja'].replace('土地臺帳事項：地番・地目・等級・地積・貸付料（圓）・備考','土地臺帳事項：地番・地目・等級・地積・備考').replace('調査事項：地番・地目・等級・地積・貸付料・備考','調査事項：地番・地目・等級・地積・貸付料（圓）・備考')
a[6]['ko']=[s.replace('토지대장 사항: 지번·지목·등급·면적·대부료(원)·비고','토지대장 사항: 지번·지목·등급·면적·비고').replace('조사사항: 지번·지목·등급·면적·대부료·비고','조사사항: 지번·지목·등급·면적·대부료(원)·비고') for s in a[6]['ko']]
a[6]['notes']=['표의 빈칸·괄호선은 이미지로 보존하고, 전사에서는 항목 관계를 풀어 적었다. 토지대장 사항의 대부료 칸에는 사선이 그어져 있으므로 기재 항목에서 제외했다. 圓은 조사사항 대부료 칸에 인쇄되어 있다.']
p.write_text(json.dumps(a,ensure_ascii=False,indent=2),encoding='utf8')

