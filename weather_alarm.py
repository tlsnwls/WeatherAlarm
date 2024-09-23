import urllib.parse
import urllib.request
import json
import pandas as pd
import datetime
import httpx
from base64 import b64encode

# API details
url = 'http://apis.data.go.kr/1360000/VilageFcstInfoService_2.0/getVilageFcst' # 단기예보 서비스
service_key = "YOUR_API_KEY"
pageNo = 1
numOfRows = 50
dataType = 'JSON'
nx = "Desired latitude"  # x-axis
ny = "Desirde longitude"  # y-axis
today = datetime.datetime.today().strftime("%Y%m%d")

# Parameters
params = {
    "serviceKey": service_key,
    "numOfRows": numOfRows,
    "pageNo": pageNo,
    "dataType": dataType,
    "base_date": today,
    "base_time": "0800",
    "nx": nx,
    "ny": ny
}

# Encode parameters
encoded_params = urllib.parse.urlencode(params)
full_url = f"{url}?{encoded_params}"

# Initialize yebo with a default value
yebo = "날씨 정보를 가져올 수 없습니다. 나중에 다시 시도해주세요."

# URL parsing and response handling
try:
    req = urllib.request.Request(full_url)
    with urllib.request.urlopen(req) as response:
        response_body = response.read().decode('utf-8')

    # Check if the response indicates a service error
    if "SERVICE ERROR" in response_body:
        raise ValueError("Service Error: The API returned a service error.")
    
    # Print the response for debugging
    print(f"Response body:\n{response_body}")

    # Parse JSON data
    data = json.loads(response_body)

    # Data processing and extraction
    df = pd.DataFrame(data['response']['body']['items']['item'])
    print(df)

    # Filter relevant weather categories
    df = df.loc[df['category'].isin(['POP', 'PTY', 'TMP','TMN','TMX','SKY'])]
    df['fsctValue'] = df['fcstValue'].astype('float', errors='ignore')
    
    df = df.pivot(index=['baseDate', 'baseTime', 'fcstDate', 'fcstTime'],
                  columns='category',
                  values='fsctValue').reset_index()
    
    df = df[df['fcstDate'] == today]
    
    # 현재 온도(8시 예보 발령 온도)
    current_temp = df.loc[df['fcstTime'] == '0900', 'TMP'].values[0] if not df.loc[df['fcstTime'] == '0900', 'TMP'].empty else None
    
    # 일 최저 기온 및 최고 기온
    min_temp = df['TMN'].min() if 'TMN' in df.columns else None
    max_temp = df['TMX'].max() if 'TMX' in df.columns else None

    # 만약 TMN, TMX가 없다면 TMP 데이터를 기반으로 직접 계산
    if pd.isna(min_temp):
        min_temp = df['TMP'].min()
    if pd.isna(max_temp):
        max_temp = df['TMP'].max()
    
    # 하늘 상태 
    sky_state = None
    if 'SKY' in df.columns:
        sky_value = df['SKY'].max()
        if sky_value == 1:
            sky_state = "맑음"
        elif sky_value == 3:
            sky_state = "구름많음"
        elif sky_value == 4:
            sky_state = "흐림"

    if not df.empty:
        df = df[df['POP'] > 30] # 강수 확률이 30% 이상인 데이터 필터링
        df['fall'] = df['PTY'].apply(lambda x: 
                             '비' if x == 1
                             else '눈/비' if x == 2
                             else '눈' if x == 3
                             else '소나기' if x == 4
                             else '없음')
        
        rain = 'or'.join(df['fall'].unique())
        prob = df['POP'].max()
        
        if pd.isna(prob):
            yebo = f"오늘은 비가 올 확률이 없다는디? 현재 기온은 {current_temp}℃, 최저 기온은 {min_temp}℃, 최고 기온은 {max_temp}℃, 하늘은 {sky_state} 이라네요!"
        else:
            yebo = f"오늘은 {rain}가 올 확률이 최대 {prob}% ! 우산 챙기기~! 현재 기온은 {current_temp}℃, 최저 기온은 {min_temp}℃, 최고 기온은 {max_temp}℃, 하늘은 {sky_state} 이라네요!"
    
    else:
        yebo = f"오늘은 비가 올 확률이 없다는디? 현재 기온은 {current_temp}℃, 최저 기온은 {min_temp}℃, 최고 기온은 {max_temp}℃, 하늘은 {sky_state} 이라네요!"
    
    print(yebo)


except urllib.error.URLError as e:
    print(f"URL error: {e.reason}")
except ValueError as e:
    print(e)
except json.JSONDecodeError as e:
    print(f"JSON decode error: {e.msg}")
    print(f"Response was:\n{response_body}")
except Exception as e:
    print(f"An unexpected error occurred: {e}")

# 카페24 호스팅 api
def sendSMS(user_id, secure, sender, receiver, message):
    endpoint = 'https://sslsms.cafe24.com/sms_sender.php'

    # Split sender's phone number into three parts
    sphone1 = sender[:3]
    sphone2 = sender[3:7]
    sphone3 = sender[7:11]

    # Join receiver numbers with a comma if there are multiple
    rphone = ','.join(receiver)
    
    # Encode the message and ensure it doesn't exceed the byte limit
    max_byte_length = 90  # 90 bytes is the limit for SMS, adjust if needed
    encoded_message = message.encode('euckr')
    
    if len(encoded_message) > max_byte_length:
        truncated_message = encoded_message[:max_byte_length]
        # Decode and re-encode to ensure no cut-off in the middle of a character
        truncated_message = truncated_message.decode('euckr', 'ignore').encode('euckr')
    else:
        truncated_message = encoded_message

    # Convert truncated_message back to string for sending
    final_message = truncated_message.decode('euckr', 'ignore')

    # Prepare the data for the POST request
    params = {
        'user_id': user_id,  # User ID
        'secure': secure,  # API Key
        'sphone1': sphone1,  # Sender's phone number parts
        'sphone2': sphone2,
        'sphone3': sphone3,
        'rphone': rphone,  # Receiver's phone number
        'msg': final_message,  # Truncated message content
        'mode': '1',  # Mode (default sending mode)
        'smsType': 'S',  # SMS type (S: short, L: long)
    }

    # Perform the POST request
    response = httpx.post(endpoint, data=params)

    # Process the response
    response_text = response.text
    print(f"Response Text: {response_text}")
    
    if response_text.startswith('success'):
        print("SMS 전송 성공")
    else:
        print("SMS 전송 실패", response_text)
    
    return response_text

# Example usage
result = sendSMS(
    user_id='Your Cafe24 account ID',
    secure='Your Cafe24 SMS API KEY',
    sender='Sender Phone Number',
    receiver=['Receiver Phone Number(form:01012341234)'],  # List of receiver numbers
    message=yebo  # Example message
)

print(result)