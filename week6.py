import math
import struct
import wave
import pyaudio
import scipy.fftpack
import numpy as np

INTMAX = 2**(32-1)-1
channels = 1
unit = 0.1
samplerate = 48000
chunk_size = 4800
padding = 10

rules = {
    'START': 512, '0': 768, '1': 896, '2': 1024, '3': 1152, '4': 1280, '5': 1408, 
    '6': 1536, '7': 1664, '8': 1792, '9': 1920, 'A': 2048, 'B': 2176, 'C': 2304, 
    'D': 2432, 'E': 2560, 'F': 2688, 'END': 2944
}
het_to_MFSK = {value: key for key, value in rules.items()}

def hex_to_audio(hex_string) :
    # Encoding text to MFSK audio
    audio = []
    for i in range(int(unit * samplerate * 2)):
        audio.append(int(INTMAX * math.sin(2 * math.pi * rules['START'] * i / samplerate)))
    for s in hex_string:
        for i in range(int(unit * samplerate * 1)):
            audio.append(int(INTMAX * math.sin(2 * math.pi * rules[s] * i / samplerate)))
    for i in range(int(unit * samplerate * 2)):
        audio.append(int(INTMAX * math.sin(2 * math.pi * rules['END'] * i / samplerate)))


    # Play audio using PyAudio
    p = pyaudio.PyAudio()
    stream = p.open(format=pyaudio.paInt32, channels=channels, rate=samplerate, output=True)
    for i in range(0, len(audio), chunk_size):
        chunk = audio[i:i+chunk_size]
        stream.write(struct.pack('<' + ('l'*len(chunk)), *chunk))
    
    return audio


def audio_to_file(audio_data, filename, samplerate=48000):
    # numpy 배열로 변환 후 32비트 정수화
    audio_data = np.array(audio_data, dtype=np.int32)
    
    with wave.open(filename, 'wb') as wf:
        wf.setnchannels(1)  # 모노 채널
        wf.setsampwidth(4)  # 32비트 (4바이트)
        wf.setframerate(samplerate)  # 샘플링 레이트 설정
        wf.writeframes(audio_data.tobytes())  # NumPy 데이터를 바이트로 변환 후 저장

# def decode_mfsk_from_audio() :
#     # Decode MFSK from audio file
#     filename = 'mfsk.wav'
#     text = ''
#     with wave.open(filename, 'rb') as w:
#         framerate = w.getframerate()
#         frames = w.getnframes()
#         audio = []
#         for i in range(frames):
#             frame = w.readframes(1)
#             d = struct.unpack('<l', frame)[0]
#             audio.append(d)
#             if len(audio) >= unit * framerate:
#                 freq = scipy.fftpack.fftfreq(len(audio), d=1/samplerate)
#                 fourier = scipy.fftpack.fft(audio)
#                 top = freq[np.argmax(abs(fourier))]
#                 data = next((k for k, v in rules.items() if v - 5 <= top <= v + 5), '')
#                 # if data == 'END':
#                 #     print() 
#                 if data and data not in {'START', 'END'}:
#                     text += data
#                     # print(data, end='')
#                 # if data == 'START':
#                 #     print(data)
#                 audio.clear()
#     decoded_text = bytes.fromhex(text).decode("utf-8")
#     print(decoded_text)


# def perform_fourier_analysis() :
#     # Fourier Transform Analysis
#     length = 5.0
#     frequencies = [261.625, 523.251, 1046.502]  # C4, C5, C6
#     volumes = [1.0, 0.75, 0.5]
#     waves = []
#     for frequency, volume in zip(frequencies, volumes):
#         wave_data = [volume * INTMAX * math.sin(2 * math.pi * frequency * i / samplerate) for i in range(int(length * samplerate))]
#         waves.append(wave_data)

#     track = [sum(values) / len(waves) for values in zip(*waves)]
#     freq = scipy.fftpack.fftfreq(len(track), d=1/samplerate)
#     fourier = scipy.fftpack.fft(track)
#     print(freq[np.argmax(abs(fourier))])

#     for i, f in enumerate(freq):
#         if 261.125 <= f <= 262.125 or 522.751 <= f <= 523.751 or 1046.002 <= f <= 1047.002:
#             print(f'{i} => {f}')


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
    hex_string = text_to_hex(user_input)
    print(f'HEX String: {hex_string}')
    audio = hex_to_audio(hex_string)

    # 🔹 생성된 Morse 오디오 데이터를 파일로 저장
    audio_to_file(audio, "mfsk.wav")
    print("Morse code audio saved as 'mfsk.wav'")



def receive_data():
    decode_mfsk_from_mic()

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
