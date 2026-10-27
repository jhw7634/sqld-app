# SQLD 오답킬러

SQLD 자격증 대비 퀴즈 웹앱 (홈 화면에 설치 가능, 오프라인 지원).

- `index.html` 앱, `questions.js` 문제은행 440문항과 이론 탭 설명(그림·비교표·외우기 팁), `manifest.webmanifest`·`sw.js`·`icon-*.png` 설치용
- `python3 check.py`: 문제 형식과 SQL 정답을 DuckDB로 검증 (`pip install duckdb`)
- 모든 문제·보기·해설·아이콘은 새로 작성했습니다. 기출·교재 문장을 옮겨 오지 않습니다.

## JS 문제집 (`js-commute/`)

자바스크립트 문제풀이 앱 (92문제, 13개 주제, 홈 화면 설치·오프라인 지원). 코드는 버튼으로 조립하고 휴대폰 안(Web Worker)에서 실행해 예시 결과와 비교해 채점합니다. 원본(문제 데이터·빌드 스크립트)은 프로젝트 폴더 `js/app/`에 있고, `python3 build.py js-commute.html pwa`로 다시 만들어 `pwa/`를 이 폴더에 복사합니다.
