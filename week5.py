import math
import statistics
import struct
import time
import pyaudio
import os
import wave
import numpy as np



code = {
    '0': '..-', '1': '.---', '2': '-..-', '3': '-...', '4': '----',
    '5': '-.--', '6': '.-..', '7': '.-.-', '8': '-.-.', '9': '---.',
    'A': '....-', 'B': '--..', 'C': '.....', 'D': '--.-', 'E': '.--.', 'F': '...-'
}

morse_to_text_map = {value: key for key, value in code.items()}

INTMAX = 2**(32-1)-1



def text_to_morse(text):
    text = text.upper()
    morse = ' '.join(code.get(char, '') for char in text if char in code)
    return morse


def hex_to_morse(hex_string):
    morse_words = [text_to_morse(char) for char in hex_string]  # 공백 없이 변환
    return ' '.join(morse_words)  # 🔹 Morse 부호를 공백 없이 변환하여 반환



def morse_to_hex(morse_code):
    # 🔹 's' 기준으로 Morse 문자 분리
    letters = morse_code.split('s')
    
    # 🔹 Morse → HEX 변환
    hex_chars = [morse_to_text_map[char] for char in letters if char in morse_to_text_map]
    
    # 🔹 HEX 문자열을 공백 없이 반환
    return ''.join(hex_chars)




def text_to_hex(text):
    hex_chars = []
    for char in text:
        hex_val = char.encode('utf-8').hex().upper()  # UTF-8 HEX 변환
        formatted_hex = ''.join([hex_val[i:i+2] for i in range(0, len(hex_val), 2)])  # HEX 데이터 붙이기
        hex_chars.append(formatted_hex)

    return ''.join(hex_chars)  # 🔹 공백 없이 HEX 문자열을 바로 반환





def hex_to_text(hex_string):
    try:
        return bytes.fromhex(hex_string).decode('utf-8')  # 🔹 HEX → UTF-8 변환
    except UnicodeDecodeError:
        print("❌ 오류: HEX 변환 중 UTF-8 디코딩 에러 발생")
        return None  # 🔹 변환 실패 시 None 반환



def morse2audio(morse):
    t = 0.1
    fs = 48000
    f = 523.251
    audio = []

    for m in morse:
        if m == '.':
            for i in range(int(t * fs)):  # 100ms 점
                audio.append(int(INTMAX * math.sin(2 * math.pi * f * (i / fs))))
        elif m == '-':
            for i in range(int(3 * t * fs)):  # 300ms 대시
                audio.append(int(INTMAX * math.sin(2 * math.pi * f * (i / fs))))
        elif m == ' ':
            for i in range(int(1 * t * fs)):  # 🔹 문자 간 공백 1유닛 해야 결과적으로 3유닛
                audio.append(0)
        

        # 🔹 각 기호 뒤에는 항상 1-unit(100ms) 공백 추가
        for i in range(int(t * fs)):
            audio.append(0)
            
    return audio


def audio2file(audio, filename):
    fs = 48000
    bit_depth = 32  # 🔹 32비트 설정
    channels = 1  # 🔹 모노

    with wave.open(filename, 'wb') as w:
        w.setnchannels(channels)  # 🔹 1채널 (모노)
        w.setsampwidth(bit_depth // 8)  # 🔹 32비트 → 4바이트 (setsampwidth(4))
        w.setframerate(fs)  # 🔹 샘플링 레이트 설정
        w.writeframes(struct.pack('<' + ('l' * len(audio)), *audio))  # 🔹 int32 변환 후 저장

    # 🔹 저장 완료 후 비트레이트 정보 출력
    bitrate = fs * bit_depth * channels  # 🔹 비트레이트 계산
    print(f"✅ Audio saved as {filename}")
    print(f"📌 Sample Rate: {fs} Hz")
    print(f"📌 Bit Depth: {bit_depth} bits")
    print(f"📌 Channels: {channels}")
    print(f"📌 Bit Rate: {bitrate / 1000} kbps")








def play_audio(audio, fs):
    p = pyaudio.PyAudio()
    stream = p.open(format=pyaudio.paInt32, channels=1, rate=fs, output=True)
    chunk_size = 4800
    for i in range(0, len(audio), chunk_size):
        chunk = audio[i:i + chunk_size]
        stream.write(struct.pack('<' + ('l'*len(chunk)), *chunk))
    stream.close()
    p.terminate()


def send_data():
    user_input = input('Input the text (Unicode): ')
    print(f'User input: {user_input}')
    hex_string = text_to_hex(user_input)
    print(f'Hex string: {hex_string}')
    morse_code = hex_to_morse(hex_string)
    print(f'Morse Code: {morse_code}')
    audio = morse2audio(morse_code)

    # 🔹 생성된 Morse 오디오 데이터를 파일로 저장
    audio2file(audio, "morse_code.wav")
    print("Morse code audio saved as 'morse_code.wav'")

    input('Press enter to play the Morse code sound!')
    play_audio(audio, 48000)

def receive_data():
    fs = 48000
    p = pyaudio.PyAudio()
    
    stream = p.open(format=pyaudio.paInt32,
                    channels=1,
                    rate=fs,
                    input=True)
    audio = []
    MORSE_THRESHOLD = 90000000
    unit = int(0.1 * fs)
    chunk_size = unit
    is_start = False
    raw_morse = ''
    silence_length = 0
    max_silence_units = 5 / 0.1

    while True:
        data = struct.unpack('<' + ('l' * chunk_size), stream.read(chunk_size))
        audio.extend(data)
        if len(audio) >= unit:
            segment = audio[:unit]
            audio = audio[unit:]
            stdev = statistics.stdev(segment)
            
            if stdev > MORSE_THRESHOLD:
                if not is_start:
                    is_start = True
                    print("Morse signal detected! Recording started...")
                
                raw_morse += '.'
                silence_length = 0
                print('Current morse : ', raw_morse)

            elif is_start:
                raw_morse += ' '
                silence_length += 1
                print('Current morse : ', raw_morse)

                if silence_length >= max_silence_units:
                    print("No signal detected for 5 seconds. Ending recording...")
                    break

    stream.stop_stream()
    stream.close()
    p.terminate()
    
    morse = raw_morse.replace('   ', 's')  
    morse = morse.replace('...', '-')
    morse = morse.replace(' ', '') 
    morse = morse.rstrip('s')  
    morse = morse.strip() 

    print('Morse Code : ', morse)
    received_hex = morse_to_hex(morse)
    print(f'Decoded HEX: {received_hex}')
    
    original_text = hex_to_text(received_hex)
    print(f'Recovered Unicode Text: {original_text}')



def main():
    while True:
        print('Morse Code over Sound with Noise')
        print('2025 SoaringTech Data Communication')
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