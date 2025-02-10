import math
import statistics
import struct
import time
import wave

import pyaudio

code = {
    '0': '-----', '1': '.----', '2': '..---', '3': '...--', '4': '....-',
    '5': '.....', '6': '-....', '7': '--...', '8': '---..', '9': '----.',
    'A': '.-', 'B': '-...', 'C': '-.-.', 'D': '-..', 'E': '.', 'F': '..-.'
}

morse_to_code = {value: key for key, value in code.items()}
INTMAX = 2**(32)-1

def text2morse(text):
    text = text.upper()
    morse = ''
    
    for t in text:
        if t == ' ':
            morse += '/'
        for key, value in code.items():
            if t == key:
                morse += value
        morse += ' '
    return morse

def morse2text(morse_code):
    words = morse_code.split('/')  # 단어 단위로 나누기
    decoded_text = ''

    for word in words:
        letters = word.split('m')  # 단어 내에서 문자 단위로 나누기
        for letter in letters:
            if letter in morse_to_code:  # 알파벳 처리
                decoded_text += morse_to_code[letter]
        decoded_text += ' '  # 단어 간 공백 추가
    return decoded_text.strip()    

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
    user_input = input('Input the text ( Unicode): ').strip()
    print(f'User input: {user_input}')

    byte_hex = user_input.encode('utf-8')
    print(byte_hex)
    byte_string = byte_hex.hex().upper()
    print(f'byte_string: {byte_string}')
    morse_code = text2morse(byte_string)
    print('Morse code: ', morse_code)
    audio = morse2audio(morse_code)
    input('Press enter to play the Morse code sound!')
    play_audio(audio,48000)


def receive_data():
    fs = 48000
    p = pyaudio.PyAudio()
    
    stream = p.open(format=pyaudio.paInt32,
                    channels=1,
                    rate=fs,
                    input=True)
    audio = []
    chunk_size = 4800 #유닛사이즈
    MORSE_THRESHOLD = 50000000

    unit = int(0.1 * fs) # 모스부호 기본단위시간
    is_start = False
    raw_morse = ''
    recording = True
    silence_length = 0

    while recording: 
        data = struct.unpack('<' + ('l'*chunk_size), stream.read(chunk_size)) 
        audio.extend(data)

        if len(audio) >= unit:
            segment = audio[:unit]
            audio = audio[unit:]
            stdev = statistics.stdev(segment)
            
            if stdev >MORSE_THRESHOLD:  # 신호 감지
                if not is_start:
                    is_start = True
                raw_morse += '.'
                silence_length = 0
                print('Current morse : ', raw_morse)
            else:
                raw_morse += ' '
                silence_length += 1
                print('Current morse : ', raw_morse)
                if silence_length >= (3/0.1):
                    recording = False               
    stream.stop_stream()
    stream.close()
    p.terminate()
    
    morse = raw_morse.replace('   ', 'm')
    morse = morse.replace('...', '-')
    morse = morse.replace(' ', '')

    print('Morse Code: ', morse)
    byte_string = morse2text(morse)
    client_byte_hex = bytes.fromhex(byte_string)
    client_byte_string = client_byte_hex.hex().upper()
    print(f'client_byte_string: {client_byte_string}')

    client_output = client_byte_hex.decode('utf-8')
    print(f'User output: {client_output}')


def main():
    while True:
        print('Unicode over Sound with Noise')
        print('2025 Spring Data Communication at CNU')
        print('[1] Send Unicode over sound(play)')
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