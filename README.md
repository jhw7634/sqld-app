# SQLD 오답킬러

SQLD 자격증 대비 퀴즈 웹앱 (홈 화면에 설치 가능, 오프라인 지원).

- `index.html` 앱, `questions.js` 문제은행 440문항과 이론 탭 설명(그림·비교표·외우기 팁), `manifest.webmanifest`·`sw.js`·`icon-*.png` 설치용
- `python3 check.py`: 문제 형식과 SQL 정답을 DuckDB로 검증 (`pip install duckdb`)
- 모든 문제·보기·해설·아이콘은 새로 작성했습니다. 기출·교재 문장을 옮겨 오지 않습니다.

## SQLD 문제집 (`commute/`)

직접 SQL을 쳐서 채점하는 출퇴근용 문제집. 설치 주소: https://jhw7634.github.io/sqld-app/commute/
원본과 빌드 스크립트는 Claude 프로젝트 파일 `sqld/app/` (`python3 build.py sqld-commute.html pwa` 결과를 그대로 복사).
