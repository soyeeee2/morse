import math
import struct
import wave
import pyaudio
import scipy.fftpack
import numpy as np
import reedsolo

# INTMAX = 2**(32-1)-1
channels = 1
UNIT = 0.1
SAMPLERATE = 48000
chunk_size = 4800
padding = 10
DATA_LEN = 24
RSC_LEN = 8
SHORTMAX = 2**(16-1)-1
PADDING_BYTE = b'\x00'  # Padding for block alignment



rules = {
    'START': 512, '0': 768, '1': 896, '2': 1024, '3': 1152, '4': 1280, '5': 1408, 
    '6': 1536, '7': 1664, '8': 1792, '9': 1920, 'A': 2048, 'B': 2176, 'C': 2304, 
    'D': 2432, 'E': 2560, 'F': 2688, 'END': 2944
}
het_to_MFSK = {value: key for key, value in rules.items()}

def text_to_audio(user_input):
    """ Encode Unicode text to MFSK audio with Reed-Solomon error correction. """
    # Step 1: Convert text to UTF-8 hex
    byte_hex = user_input.encode('utf-8')
    string_hex = byte_hex.hex().upper()
    print(f'reedsolo 전: {string_hex}')

    audio = []
    encoded_data_list = []

    # Step 2: Add start signal
    for i in range(int(UNIT * SAMPLERATE * 2)):
        audio.append(SHORTMAX * math.sin(2 * math.pi * rules['START'] * i / SAMPLERATE))

    # Step 3: Reed-Solomon Encoding with Padding
    client_rsc = reedsolo.RSCodec(RSC_LEN)

    for k in range(0, len(byte_hex), DATA_LEN):
        data = byte_hex[k:k+DATA_LEN]

        # If block is smaller than DATA_LEN, add padding
        if len(data) < DATA_LEN:
            data = data.ljust(DATA_LEN, PADDING_BYTE)  

        # 🔹 Ensure Reed-Solomon encoding applies to all blocks (even padded ones)
        encoded_data = client_rsc.encode(data).hex().upper()
        encoded_data_list.append(encoded_data)
        print(f'encoded_data: {encoded_data}')

        # Convert encoded hex to audio signal
        for s in encoded_data:
            if s in rules:
                freq = rules[s]
                for i in range(int(UNIT * SAMPLERATE)):
                    audio.append(SHORTMAX * math.sin(2 * math.pi * freq * i / SAMPLERATE))

    # Step 4: Add end signal
    for i in range(int(UNIT * SAMPLERATE * 2)):
        audio.append(SHORTMAX * math.sin(2 * math.pi * rules['END'] * i / SAMPLERATE))

    # 🔹 전체 `encoded_data`를 하나의 문자열로 합쳐서 최종 출력
    full_encoded_data = ''.join(encoded_data_list)
    print(f'전체 encoded_data: {full_encoded_data}') 

    return audio

def audio_to_file(audio_data, filename, samplerate=48000):
    # numpy 배열로 변환 후 32비트 정수화
    audio_data = np.array(audio_data, dtype=np.int32)
    
    with wave.open(filename, 'wb') as wf:
        wf.setnchannels(1)  # 모노 채널
        wf.setsampwidth(4)  # 32비트 (4바이트)
        wf.setframerate(samplerate)  # 샘플링 레이트 설정
        wf.writeframes(audio_data.tobytes())  # NumPy 데이터를 바이트로 변환 후 저장




def file_to_audio(filename='200802013.wav'):
    """ Decode MFSK from 64-bit audio and recover Unicode text using Reed-Solomon """
    DATA_LEN = 12  # 데이터 12개 (6바이트)
    RSC_LEN = 4  # 오류 정정 4개 (2바이트)
    BLOCK_SIZE = 8  # 총 8바이트 (16개 HEX 문자열)

    client_rsc = reedsolo.RSCodec(RSC_LEN)
    received_hex = ""  # 전체 HEX 데이터 저장

    # Read 64-bit WAV file
    with wave.open(filename, 'rb') as w:
        framerate = w.getframerate()
        frames = w.getnframes()

        for i in range(frames):  # 1 프레임(샘플)씩 읽음 (8바이트)
            frame = w.readframes(8)  # 8바이트(64비트) 읽기

            # 🔹 8바이트(64비트)를 16개의 HEX 문자열로 변환
            hex_value = frame.hex().upper()  # 직접 HEX 변환 (8바이트 → 16개 HEX)
            received_hex += hex_value  # 전체 HEX 문자열 저장

    # Reed-Solomon 디코딩 후 원본 데이터 복원
    final_decoded_hex = ""  # 최종 HEX 데이터 저장

    for i in range(0, len(received_hex), BLOCK_SIZE * 2):  # 8바이트(16 HEX) 블록 단위로 처리
        block_hex = received_hex[i:i + (BLOCK_SIZE * 2)]  # 한 블록 추출
        block_bytes = bytes.fromhex(block_hex)  # HEX → 바이트 변환

        # 🔹 블록 크기가 부족해도 그대로 진행
        if len(block_bytes) > RSC_LEN:  # RSC_LEN(2바이트)보다 큰 경우만 처리
            try:
                decoded_block = client_rsc.decode(block_bytes)  # Reed-Solomon 복원
                original_data = decoded_block[:-RSC_LEN]  # 마지막 2바이트 제거

                final_decoded_hex += original_data.hex()  # HEX 문자열로 변환 후 저장

            except reedsolo.ReedSolomonError:
                print(f"❌ 오류 정정 실패: {block_hex}")  # 디버깅용 출력
                continue  # 오류 정정 실패한 블록은 건너뜀

    # UTF-8 변환
    try:
        decoded_text = bytes.fromhex(final_decoded_hex).decode("utf-8")
        print(f"✅ 최종 복원된 텍스트: {decoded_text}")
        return decoded_text
    except UnicodeDecodeError:
        print("❌ UTF-8 디코딩 실패: 데이터 손상 가능")
        return None


def hex_to_text(hex_string):
    try:
        return bytes.fromhex(hex_string).decode('utf-8')
    except UnicodeDecodeError:
        print("❌ 오류: HEX 변환 중 UTF-8 디코딩 에러 발생")
        return None
    
def text_to_hex(text):
    hex_chars = []
    for char in text:
        hex_val = char.encode('utf-8').hex().upper()  # UTF-8 HEX 변환
        formatted_hex = ''.join([hex_val[i:i+2] for i in range(0, len(hex_val), 2)])  # HEX 데이터 붙이기
        hex_chars.append(formatted_hex)

    return ''.join(hex_chars)  # 🔹 공백 없이 HEX 문자열을 바로 반환



def decode_mfsk_from_mic():
    """ 실시간으로 마이크에서 MFSK 신호를 수신하고 디코딩하는 함수 """
    p = pyaudio.PyAudio()
    stream = p.open(format=pyaudio.paInt32, channels=1, rate=samplerate, input=True, frames_per_buffer=chunk_size)
    
    print("🎤 Listening for MFSK signals... (Press Ctrl+C to stop)")
    
    text = ""
    last_char = None  # 중복 문자 방지
    start_detected = False  # START 중복 감지 방지


    try:
        while True:
            data = stream.read(chunk_size)  # 1 unit(0.1초) 크기로 마이크에서 데이터 읽기
            audio = np.frombuffer(data, dtype=np.int32)  # 바이트 데이터를 32비트 정수 배열로 변환

            # ✅ 퓨리에 변환 (FFT) 수행
            freq = scipy.fftpack.fftfreq(len(audio), d=1/samplerate)
            fourier = scipy.fftpack.fft(audio)
            top_freq = freq[np.argmax(abs(fourier))]  # 가장 강한 주파수 찾기
            
            print(f"🔍 Detected Frequency: {top_freq:.2f} Hz")  # 감지된 주파수 출력

            # ✅ 감지된 주파수를 MFSK 주파수와 매핑
            data_char = next((k for k, v in rules.items() if v - padding <= top_freq <= v + padding), '')

            # ✅ 실시간 디코딩 로직
            if data_char == "START":
                print("\n🔹 Start Signal Detected")
                text = ""  # 새로운 메시지 시작
            elif data_char == "END":
                print(text)
                print("\n✅ Decoded Message:", bytes.fromhex(text).decode("utf-8"))
                break  # 메시지 수신 완료 후 종료
            elif data_char:
                text += data_char  # HEX 데이터 추가
                print(data_char, end='', flush=True)

    except KeyboardInterrupt:
        print("\n🛑 Stopped Listening.")

    stream.stop_stream()
    stream.close()
    p.terminate()



def send_data():
    user_input = input('Input the text (Unicode): ')
    print(f'User input: {user_input}')
    audio = text_to_audio(user_input)

    # 🔹 생성된 Morse 오디오 데이터를 파일로 저장
    audio_to_file(audio, "mfsk.wav")
    print("Morse code audio saved as 'mfsk.wav'")



def receive_data():
    file_to_audio()

# def receive_test():
#     decode_mfsk_from_audio()



def main():
    while True:
        print('2024 Spring Data Communication at CNU')
        print('[1] Send Unicode over sound (play)')
        print('[2] Receive Unicode over sound (record)')
        print('[q] Exit')
        select = input('Select menu: ').strip().upper()
        if select == '1':
            send_data()
        elif select == '2':
            receive_data()
        elif select == 'Q':
            print('Terminating...')
            break

if __name__ == '__main__':
    main()
