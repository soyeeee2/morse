import math
import statistics
import struct
import time
import pyaudio
import os


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
        morse_words.append(" ".join(morse_chars))  

    return "   ".join(morse_words) 


def morse_to_hex(morse_code):
    morse_code = morse_code.replace("       ", "m")  # 단어 구분
    morse_code = morse_code.replace("   ", "s")  # 문자 구분

    words = morse_code.split("m")  # 단어 단위로 나누기
    hex_string_list = []

    for word in words:
        letters = word.strip().split("s")
        hex_chars = [morse_to_text_map[char] for char in letters if char in morse_to_text_map]
        if hex_chars:
            hex_string_list.append(" ".join(hex_chars))  # HEX 문자열로 변환

    return "   ".join(hex_string_list)


def text_to_hex(text):
    hex_chars = []
    for char in text:
        if char == " ":
            hex_chars.append("       ")  # 단어 구분 7-unit 공백
        else:
            hex_val = char.encode('utf-8').hex().upper()
            formatted_hex = ' '.join(hex_val[i:i+2] for i in range(0, len(hex_val), 2))
            hex_chars.append(formatted_hex)
    return '   '.join(hex_chars)  # 문자 간 3-unit 공백 유지



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
    hex_string = text_to_hex(user_input)
    print(f'Hex string: {hex_string}')
    morse_code = hex_to_morse(hex_string)
    print(f'Morse Code: {morse_code}')
    audio = morse_to_audio(morse_code)
    input('Press enter to play the Morse code sound!')
    play_audio(audio, 48000)

def receive_data(raw_morse):
    # fs = 48000
    # p = pyaudio.PyAudio()
    
    # stream = p.open(format=pyaudio.paInt32,
    #                 channels=1,
    #                 rate=fs,
    #                 input=True)
    # audio = []
    # MORSE_THRESHOLD = 80000000
    # unit = int(0.1 * fs)
    # chunk_size = unit
    # is_start = False
    # raw_morse = ''
    # silence_length = 0
    # max_silence_units = 5 / 0.1

    # while True:
    #     data = struct.unpack('<' + ('l' * chunk_size), stream.read(chunk_size))
    #     audio.extend(data)
    #     if len(audio) >= unit:
    #         segment = audio[:unit]
    #         audio = audio[unit:]
    #         stdev = statistics.stdev(segment)
            
    #         if stdev > MORSE_THRESHOLD:
    #             if not is_start:
    #                 is_start = True
    #                 print("Morse signal detected! Recording started...")
                
    #             raw_morse += '.'
    #             silence_length = 0
    #             print('Current morse : ', raw_morse)

    #         elif is_start:
    #             raw_morse += ' '
    #             silence_length += 1
    #             print('Current morse : ', raw_morse)

    #             if silence_length >= max_silence_units:
    #                 print("No signal detected for 5 seconds. Ending recording...")
    #                 break

    # stream.stop_stream()
    # stream.close()
    # p.terminate()
    
    morse = raw_morse.replace('       ', 'm')  
    morse = morse.replace('   ', 's')  
    morse = morse.replace('...', '-')    

    print('Morse Code : ', morse)
    received_hex = morse_to_hex(morse)
    print(f'Decoded HEX: {received_hex}')
    
    original_text = hex_to_text(received_hex)
    print(f'Recovered Unicode Text: {original_text}')



def main():
    # while True:
    #     print('Morse Code over Sound with Noise')
    #     print('2025 SoaringTech Data Communication')
    #     print('[1] Send Unicode over sound (play)')
    #     print('[2] Receive Unicode over sound (record)')
    #     print('[q] Exit')
    #     select = input('Select menu: ').strip().upper()
    #     if select == '1':
    #         send_data()
    #     elif select == '2':
    #         receive_data()
    #     elif select == 'Q':
    #         print('Terminating...')
    #         break
    receive_data('.--. ..... ---. -.-- -.-. -.-.   .--. --.. -.-. -.-- ---. -.--            .--. --.- ---. -.-- ---. .....   .--. ....- --.. -.-. -.-. ..-')


if __name__ == '__main__':
    main()