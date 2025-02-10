import math
import statistics
import struct
import time
import pyaudio
import os

# Ensure pyaudio is installed
try:
    import pyaudio
except ImportError:
    os.system("pip install pyaudio")
    import pyaudio

code = {
    '0': '..-', '1': '.---', '2': '-..-', '3': '-...', '4': '----',
    '5': '-.--', '6': '.-..', '7': '.-.-', '8': '-.-.', '9': '---.',
    'A': '....-', 'B': '--..', 'C': '.....', 'D': '--.-', 'E': '.--.', 'F': '...-'
}

morse_to_text_map = {value: key for key, value in code.items()}


def text_to_morse(text):
    text = text.upper()
    morse = ' '.join(code.get(char, '') for char in text if char in code)
    return morse


def hex_to_morse(hex_string):
    hex_groups = hex_string.split("   ")  # 문자 단위로 구분 (3-unit 공백)
    morse_words = []  

    for group in hex_groups:
        hex_chars = group.split()  # HEX를 2자리 단위로 나누기
        morse_chars = [text_to_morse(char) for char in hex_chars]  # 각 HEX를 모스로 변환
        morse_words.append("   ".join(morse_chars))  # 문자 간 3-unit 공백 적용

    return "       ".join(morse_words)  # 단어 간 7-unit 공백 적용



def morse_to_text(morse_code):
    words = morse_code.split("       ")  # 7-unit 공백 → 단어 구분
    decoded_text = ''
    
    for word in words:
        letters = word.split("   ")  # 3-unit 공백 → 문자 구분
        for letter in letters:
            if letter in morse_to_text_map:  # 변환 가능하면 변환
                decoded_text += morse_to_text_map[letter]
        decoded_text += ' '  # 단어 간 공백 추가
    
    return decoded_text.strip()  # 마지막 공백 제거


def text_to_hex(text):
    return '       '.join(['   '.join(char.encode('utf-8').hex().upper()[i] + ' ' + char.encode('utf-8').hex().upper()[i+1] for i in range(0, len(char.encode('utf-8').hex()), 2)) for char in text])


def hex_to_text(hex_string):
    return ''.join([bytes.fromhex(part).decode('utf-8') for part in hex_string.split()])  # 공백 기준으로 복원


def morse_to_audio(morse):
    INTMAX = 2**(32-1)-1
    t = 0.1
    fs = 48000
    f = 523.251
    audio = []
    for m in morse:
        if m == '.':
            for i in range(int(t*fs*1)):
                audio.append(int(INTMAX*math.sin(2*math.pi*f*(i/fs))))
        elif m == '-':
            for i in range(int(t*fs*3)):
                audio.append(int(INTMAX*math.sin(2*math.pi*f*(i/fs))))
        elif m == ' ':
            for i in range(int(t*fs*3)):
                audio.append(int(0))
        for i in range(int(t*fs*1)):
            audio.append(int(0))
    return audio


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
    byte_string = text_to_hex(user_input)
    print(f'Hex string: {byte_string}')
    morse_code = hex_to_morse(byte_string)
    print(f'Morse Code: {morse_code}')
    audio = morse_to_audio(morse_code)
    input('Press enter to play the Morse code sound!')
    play_audio(audio, 48000)


def receive_data():
    hex_string = input('Enter received Morse Code (for testing purposes): ')
    received_text = hex_to_text(hex_string)
    print(f'Decoded Text: {received_text}')


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
