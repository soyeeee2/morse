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
padding = 10
SHORTMAX = 2**(16-1)-1
PADDING_BYTE = b'\x00'  # Padding for block alignment


DATA_LEN = 12  # 데이터 블록 길이
RSC_LEN = 4  # Reed-Solomon 오류 정정 길이
BLOCK_SIZE = DATA_LEN + RSC_LEN  # 16바이트 (32 HEX)
UNIT = 0.1  # 1유닛(0.1초)
SAMPLERATE = 48000
chunk_size = 2 # 32비트형식(4바이트 * 2)


rules = {
    'START': 512, '0': 768, '1': 896, '2': 1024, '3': 1152, '4': 1280, '5': 1408, 
    '6': 1536, '7': 1664, '8': 1792, '9': 1920, 'A': 2048, 'B': 2176, 'C': 2304, 
    'D': 2432, 'E': 2560, 'F': 2688, 'END': 2944
}
hex_to_MFSK = {value: key for key, value in rules.items()}

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
    client_rsc = reedsolo.RSCodec(RSC_LEN, nsize=16)

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

# def file_to_audio(filename='200802013.wav'):
#     """ MFSK WAV 파일에서 START/END 신호를 감지하고 데이터를 복원 """
#     client_rsc = reedsolo.RSCodec(RSC_LEN)  # Reed-Solomon 복원기
#     received_hex = ""  # HEX 데이터 저장
#     final_decoded_bytes = b""  # 최종 UTF-8 복원 바이트 데이터

#     with wave.open(filename, 'rb') as w:
#         sample_width = w.getsampwidth()  # 샘플 크기 확인
#         bit_depth = sample_width * 8  # 바이트 → 비트 변환

#         print(f"🔍 Detected Sample Width: {sample_width} bytes ({bit_depth}-bit WAV file)")
#         framerate = w.getframerate()
#         frames = w.getnframes()

#         # START/END 감지용 변수
#         start_detected = 0  
#         end_detected = 0  
#         recording = False  # 데이터 수집 여부

#         for i in range(0, frames, chunk_size):
#             frame = w.readframes(chunk_size)
#             if len(frame) < chunk_size:  
#                 break  # 파일 끝 도달

#             # 64비트 PCM 데이터를 16비트 정수 배열로 변환
#             audio = np.frombuffer(frame, dtype=np.int16)

#             # FFT 변환 수행
#             freq = scipy.fftpack.fftfreq(len(audio), d=1/SAMPLERATE)
#             fourier = scipy.fftpack.fft(audio)
#             top_freq = freq[np.argmax(abs(fourier))]  # 가장 강한 주파수

#             # 감지된 주파수를 MFSK 주파수로 매핑
#             detected_char = next((k for k, v in rules.items() if v - padding <= top_freq <= v + padding), '')

#             # START 신호 감지 (2유닛 연속)
#             if detected_char == "START":
#                 start_detected += 1
#                 if start_detected == 2:
#                     print("\n🔹 START 신호 감지됨 - 데이터 수집 시작")
#                     recording = True
#                     received_hex = ""  # 데이터 초기화
#                     continue
#             else:
#                 start_detected = 0  # 중간에 끊기면 초기화

#             # END 신호 감지 (2유닛 연속)
#             if detected_char == "END":
#                 end_detected += 1
#                 if end_detected == 2:
#                     print("\n✅ END 신호 감지됨 - 데이터 수집 종료")
#                     recording = False
#                     break
#             else:
#                 end_detected = 0  # 중간에 끊기면 초기화

#             # 데이터 수집 중이라면 HEX 값 저장
#             if recording and detected_char and detected_char not in ["START", "END"]:
#                 received_hex += detected_char
#                 print(detected_char, end='', flush=True)  # 실시간 출력

#     print(f"\n🔍 수집된 HEX 데이터: {received_hex}")

#     # ✅ Reed-Solomon 디코딩
#     for i in range(0, len(received_hex), BLOCK_SIZE * 2):
#         block_hex = received_hex[i:i + (BLOCK_SIZE * 2)]
#         block_bytes = bytes.fromhex(block_hex)

#         try:
#             decoded_block = client_rsc.decode(block_bytes)  # Reed-Solomon 복원

#             # 튜플 반환 시 첫 번째 요소 사용
#             original_data = decoded_block if not isinstance(decoded_block, tuple) else decoded_block[0]

#             # 마지막 RSC_LEN(4바이트) 제거
#             original_data = original_data[:-RSC_LEN]
#             final_decoded_bytes += original_data
#         except reedsolo.ReedSolomonError:
#             print(f"❌ Reed-Solomon 복원 실패: {block_hex}")
#             continue

#     # ✅ UTF-8 변환
#     try:
#         decoded_text = final_decoded_bytes.decode("utf-8")
#         print(f"\n✅ 최종 복원된 텍스트: {decoded_text}")
#         return decoded_text
#     except UnicodeDecodeError:
#         print("❌ UTF-8 디코딩 실패: 데이터 손상 가능")
#         return None

def file_to_audio(filename='200802013.wav'):
    """ 32비트 PCM WAV 파일에서 8바이트(64비트) 단위로 데이터를 읽고 MFSK 복원 """
    client_rsc = reedsolo.RSCodec(RSC_LEN)  # Reed-Solomon 복원기
    received_hex = ""  # HEX 데이터 저장
    final_decoded_bytes = b""  # 최종 UTF-8 복원 바이트 데이터

    with wave.open(filename, 'rb') as w:
        sample_width = w.getsampwidth()  # 샘플 크기 확인
        bit_depth = sample_width * 8  # 바이트 → 비트 변환

        print(f"🔍 Detected Sample Width: {sample_width} bytes ({bit_depth}-bit WAV file)")

        framerate = w.getframerate()
        frames = w.getnframes()

        start_detected = 0  
        end_detected = 0  
        recording = False  

        for i in range(0, frames, chunk_size):
            frame = w.readframes(chunk_size)  # ✅ 8바이트(2개의 32비트 샘플)씩 읽기
            if len(frame) < chunk_size * 4:  
                break  # 파일 끝 도달

            # ✅ 32비트(4바이트) 샘플 2개를 합쳐서 64비트로 해석
            audio = np.frombuffer(frame, dtype=np.int16)


            print(f"🎵 Raw Audio Data: {audio[:10]}")

            # FFT 수행
            freq = scipy.fftpack.fftfreq(len(audio), d=1/SAMPLERATE)
            fourier = scipy.fftpack.fft(audio)
            top_freq = freq[np.argmax(abs(fourier))]  # 가장 강한 주파수

            # 감지된 주파수를 MFSK 주파수로 매핑
            detected_char = next((k for k, v in rules.items() if v - padding <= top_freq <= v + padding), '')

            # ✅ 실시간 출력
            print(f"📡 [{i // chunk_size}] Detected Frequency: {top_freq:.2f} Hz → {detected_char}")

            # START 신호 감지 (2유닛 연속)
            if detected_char == "START":
                start_detected += 1
                if start_detected == 2:
                    print("\n🔹 START 신호 감지됨 - 데이터 수집 시작")
                    recording = True
                    received_hex = ""  # 데이터 초기화
                    continue
            else:
                start_detected = 0  # 중간에 끊기면 초기화

            # END 신호 감지 (2유닛 연속)
            if detected_char == "END":
                end_detected += 1
                if end_detected == 2:
                    print("\n✅ END 신호 감지됨 - 데이터 수집 종료")
                    recording = False
                    break
            else:
                end_detected = 0  # 중간에 끊기면 초기화

            # 데이터 수집 중이라면 HEX 값 저장
            if recording and detected_char and detected_char not in ["START", "END"]:
                received_hex += detected_char
                print(detected_char, end='', flush=True)  # 실시간 출력

    print(f"\n🔍 수집된 HEX 데이터: {received_hex}")

    # ✅ Reed-Solomon 디코딩
    for i in range(0, len(received_hex), BLOCK_SIZE * 2):
        block_hex = received_hex[i:i + (BLOCK_SIZE * 2)]
        block_bytes = bytes.fromhex(block_hex)

        try:
            decoded_block = client_rsc.decode(block_bytes)  # Reed-Solomon 복원

            # 튜플 반환 시 첫 번째 요소 사용
            original_data = decoded_block if not isinstance(decoded_block, tuple) else decoded_block[0]

            # 마지막 RSC_LEN(4바이트) 제거
            original_data = original_data[:-RSC_LEN]
            final_decoded_bytes += original_data
        except reedsolo.ReedSolomonError:
            print(f"❌ Reed-Solomon 복원 실패: {block_hex}")
            continue

    # ✅ UTF-8 변환
    try:
        decoded_text = final_decoded_bytes.decode("utf-8")
        print(f"\n✅ 최종 복원된 텍스트: {decoded_text}")
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
