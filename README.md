# WeatherAlarm

##  날씨 API: Open-Meteo API 사용
- https://open-meteo.com/ 
- 사용 방법 심플
- 호출 시점 가장 최근 예보 시점으로 날씨 데이터를 제공

## 문자 API: 카페24 문자 호스팅 API 사용
- weather_alarm.py 참고

## 사용방법
- git clone
- python -m venv venv(권장) -> source venv/bin/activate -> pip install -r requirements.txt
- CAFE24에서 신청한 문자 API에 대한 APIKEY, 사용자 아이디 등을 weather_alarm.py 알맞은 부분에 기입
- open-meteo에서 생성한 날씨 API 주소를 기입, 위.경도는 원하는 곳으로 바꿔서 입력해도 됨
- 수신자에게 보낼 문자 형식 수정 