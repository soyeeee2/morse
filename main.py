import math
import statistics
import struct
import time
import wave

import pyaudio


english = {
    'A': '.-', 'B': '-...', 'C': '-.-.', 'D': '-..', 'E': '.', 'F': '..-.',
    'G': '--.', 'H': '....', 'I': '..', 'J': '.---', 'K': '-.-', 'L': '.-..',
    'M': '--', 'N': '-.', 'O': '---', 'P': '.--.', 'Q': '--.-', 'R': '.-.',
    'S': '...', 'T': '-', 'U': '..-', 'V': '...-', 'W': '.--', 'X': '-..-',
    'Y': '-.--', 'Z': '--..'
}

number = {
    '1': '.----', '2': '..---', '3': '...--', '4': '....-', '5': '.....',
    '6': '-....', '7': '--...', '8': '---..', '9': '----.', '0': '-----'
}


morse_to_english = {value: key for key, value in english.items()}
morse_to_number = {value: key for key, value in number.items()}


def text2morse(text):
    text = text.upper()
    morse = ''
    
    for t in text:
        if t == ' ':
            morse += '/'
        for key, value in english.items():
            if t == key:
                morse += value
        for key, value in number.items():
            if t == key:
                morse += value
        morse += ' '
    return morse


def morse2audio(morse):
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
    stream = p.open(format=pyaudio.paInt32,
                    channels=1,
                    rate=fs,
                    output=True)
    chunk_size = 4800
    for i in range(0, len(audio), chunk_size):
        chunk = audio[i:i + chunk_size]
        stream.write(struct.pack('<' + ('l'*len(chunk)), *chunk))
    stream.close()
    p.terminate()


def send_data():
    print('Type some text (only English and Number)')
    user_input = input('User_input: ').strip().upper()
    print(user_input)
    morse_code = text2morse(user_input)
    print('Morse code: ', morse_code)
    audio = morse2audio(morse_code)
    input('Press enter to play the Morse code sound!')
    play_audio(audio,48000)


def morse2text(morse_code):
    words = morse_code.split('s')  # 단어 단위로 나누기
    decoded_text = ''
    for word in words:
        letters = word.split('m')  # 단어 내에서 문자 단위로 나누기
        for letter in letters:
            if letter in morse_to_english:  # 알파벳 처리
                decoded_text += morse_to_english[letter]
            elif letter in morse_to_number:  # 숫자 처리
                decoded_text += morse_to_number[letter]
        decoded_text += ' '  # 단어 간 공백 추가
    return decoded_text.strip()

def receive_data():
    fs = 48000
    p = pyaudio.PyAudio()
    
    stream = p.open(format=pyaudio.paInt32,
                    channels=1,
                    rate=fs,
                    input=True)
    audio = []
    MORSE_THRESHOLD = 80000000

    unit = int(0.1 * fs)  # 모스 부호 기본 단위시간 (100ms)
    chunk_size = unit
    is_start = False  # 첫 신호 감지 여부
    raw_morse = ''
    silence_length = 0
    max_silence_units = 5 / 0.1  # 5초 동안 입력이 없으면 종료 (5초 / 0.1초 단위)

    while True:
        data = struct.unpack('<' + ('l' * chunk_size), stream.read(chunk_size)) 
        audio.extend(data)

        if len(audio) >= unit:
            segment = audio[:unit]
            audio = audio[unit:]
            stdev = statistics.stdev(segment)
            
            if stdev > MORSE_THRESHOLD:  # 신호 감지됨
                if not is_start:
                    is_start = True  # 첫 신호 감지 후 시작 상태 설정
                    print("Morse signal detected! Recording started...")
                
                raw_morse += '.'
                silence_length = 0  # 소리 감지 시 침묵 길이 초기화
                print('Current morse : ', raw_morse)

            elif is_start:  # 신호 감지된 이후에만 침묵 카운트 시작
                raw_morse += ' '
                silence_length += 1
                print('Current morse : ', raw_morse)

                if silence_length >= max_silence_units:  # 5초 동안 신호가 없으면 종료
                    print("No signal detected for 5 seconds. Ending recording...")
                    break

    stream.stop_stream()
    stream.close()
    p.terminate()
    
    # 🔹 순차적으로 변환해야 replace가 정상적으로 동작함
    morse = raw_morse.replace('...', '-')
    morse = morse.replace('       ', 's')
    morse = morse.replace('   ', 'm')
    # morse = morse.replace('m', '')
    # morse = morse.replace('s', ' ')

    print('Morse Code : ', morse)
    print('Text : ', morse2text(morse))


def main():
    while True:
        print('Morse Code over Sound with noise')
        print('2025 SoaringTech Data Communication')
        print('[1] Send morse code over sound (play)')
        print('[2] Receive morse code over sound (record)')
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