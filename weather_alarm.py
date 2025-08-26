"""
선택한 데이터 목록:
- Daily Weather Variables: Maximum Temperature (2 m), Minimum Temperature (2 m)
- Current Weather: Temperature (2 m), Apparent Temperature, Wind Speed (10 m), Precipitation, Rain, Showers, Snowfall, Cloud cover Total
"""
import httpx

# -------------------[ 설정 부분 ]-------------------
LATITUDE=111.111111 # 날씨를 알고싶은 위치의 위도
LONGTITUDE=222.22222 # 날씨를 알고싶은 위치의 경도
API_URL = f"https://api.open-meteo.com/v1/forecast?latitude={LATITUDE}&longitude={LONGTITUDE}&daily=temperature_2m_max,temperature_2m_min&models=kma_seamless&current=temperature_2m,rain,cloud_cover,wind_speed_10m,showers,snowfall,precipitation,apparent_temperature&timezone=Asia%2FTokyo&forecast_days=1"
SMS_USER_ID = 'YOUR_CAFE24_ID'
SMS_SECURE_KEY = 'YOUR_CAFE24_SMS_API_KEY'
SMS_SENDER = 'YOUR_SENDER_PHONE_NUMBER'
SMS_RECEIVERS = ['010xxxxxxxx'] # Example) 01012341234, 01056785678... 배열 안에 콤마로 구분
# ----------------------------------------------------

def get_weather_data(url):
    print("날씨 API를 호출하여 최신 정보를 가져옵니다...")
    try:
        with httpx.Client() as client:
            response = client.get(url)
            response.raise_for_status()
            print("API 호출 성공!")
            return response.json()
    except Exception as e:
        print(f"API 호출 중 오류 발생: {e}")
        return None

def parse_weather_and_create_message(data):
    """
    Open-Meteo JSON 데이터를 파싱하여 이모티콘 없는 날씨 요약 메시지를 생성
    """
    try:
        daily_info = data['daily']
        current_info = data['current']
        max_temp = daily_info['temperature_2m_max'][0]
        min_temp = daily_info['temperature_2m_min'][0]
        apparent_temp = current_info['apparent_temperature']
        
        # 강수, 강설, 바람 세기, 구름 정보 추출
        precipitation = current_info.get('precipitation', 0.0)
        showers = current_info.get('showers', 0.0)
        snowfall = current_info.get('snowfall', 0.0)
        wind_speed = current_info.get('wind_speed_10m', 0.0)
        cloud_cover = current_info.get('cloud_cover', 0)
        
        # 구름 양(%)에 따라 하늘 상태 결정
        if cloud_cover <= 30:
            sky_condition = "맑음"
        elif cloud_cover <= 80:
            sky_condition = "구름 많음"
        else:
            sky_condition = "흐림"
        
        if snowfall > 0:
            # 눈 소식이 있을 때의 메시지
            umbrella_recommendation = f"오늘은 눈이 내려요! (예상 적설량 {snowfall}cm) 길이 미끄러울 수 있으니 조심하시고 따뜻하게 챙겨입으세요~"
        elif precipitation > 0 or showers > 0:
            # 비 소식이 있을 때의 메시지
            umbrella_recommendation = f"오늘은 비/소나기 소식이 있어요. (강수량 {precipitation+showers}mm) 외출 시 우산 꼭 챙기세요~"
        else:
            # 비 소식이 없을 때의 메시지
            umbrella_recommendation = "오늘은 비 소식 없이 맑아요! 가벼운 하루 보내시고 화이팅이에요. 으라차차!"
            
        # 이모티콘 대신 텍스트와 기호로 메시지 재구성
        message = (
            f"날씨 알림봇\n"
            f"오늘의 날씨!\n\n"
            f"[하늘] {sky_condition}(구름 {cloud_cover}%)\n"
            f"[온도] 최고 {max_temp}℃ / 최저 {min_temp}℃\n"
            f"[체감] 현재 {apparent_temp}℃ 에요. \n"
            f"[바람] {wind_speed} km/h \n\n"
            f"{umbrella_recommendation}"
        )
        return message
    except (KeyError, IndexError) as e:
        print(f"JSON 데이터 파싱 중 오류 발생: {e}")
        return "날씨 정보를 처리하는 데 실패했습니다."

def sendSMS(user_id, secure, sender, receiver, message):
    """
    메시지 길이에 따라 SMS 또는 LMS로 자동 선택 후 전송
    """
    endpoint = 'https://sslsms.cafe24.com/sms_sender.php'
    sphone1, sphone2, sphone3 = sender[:3], sender[3:7], sender[7:11]
    rphone = ','.join(receiver)
    
    # EUC-KR로 인코딩 불가능한 문자(이모지 등)를 제거
    safe_message = ''.join(c for c in message if c.encode('euckr', 'ignore'))
    
    # 길이에 따라 메시지 타입 결정
    encoded_message_euckr = safe_message.encode('euckr')
    if len(encoded_message_euckr) <= 90:
        print("단문 메시지(SMS) 방식으로 전송합니다.")
        sms_type = 'S'
    else:
        print("장문 메시지(LMS) 방식으로 전송합니다.")
        sms_type = 'L'

    params = {
        'user_id': user_id,
        'secure': secure,
        'sphone1': sphone1,
        'sphone2': sphone2,
        'sphone3': sphone3,
        'rphone': rphone,
        'msg': safe_message,
        'mode': '1',
        'smsType': sms_type,
        # 'testflag' : 'Y' # Test시 활성화: 문자를 송신하진 않음.
    }
    
    try:
        response = httpx.post(endpoint, data=params)
        response.raise_for_status()
        print(f"API 응답: {response.text}")
        return response.text
    except httpx.RequestError as e:
        print(f"전송 요청 실패: {e}")
        return f"RequestError: {e}"

if __name__ == "__main__":
    weather_data = get_weather_data(API_URL)
    
    if weather_data:
        yebo_message = parse_weather_and_create_message(weather_data)
        print("생성된 최종 메시지:\n" + "="*20)
        print(yebo_message)
        print("="*20 + "\n")

        print("SMS 전송을 시작합니다...")
        sendSMS(
            user_id=SMS_USER_ID,
            secure=SMS_SECURE_KEY,
            sender=SMS_SENDER,
            receiver=SMS_RECEIVERS,
            message=yebo_message
        )
    else:
        print("날씨 데이터를 가져오지 못했으므로 SMS 전송을 중단합니다.")