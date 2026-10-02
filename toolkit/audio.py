import io
import threading
import time
import urllib.request
import wave
import winsound

CHANNELS = 2
SAMPLE_WIDTH = 2
SAMPLE_RATE = 44100

input_wav_path = r'../assets/source_audio/printer_noise.wav'
raw_output_path = r'../assets/generated/printer_noise_audio_bytes'

audio_library = {'ds9_ops_button_1': r'https://github.com/Kaz95/stdlib-only-toolkit/raw/refs/heads/dev/assets'
                                     r'/generated/ds9_ops_button_1_audio_bytes',

                 'cash_register': r'https://github.com/Kaz95/stdlib-only-toolkit/raw/refs/heads/dev/assets/generated'
                                  r'/kaching_audio_bytes',

                 'printer': r'https://github.com/Kaz95/stdlib-only-toolkit/raw/refs/heads/dev/assets/generated'
                            r'/printer_noise_audio_bytes'}


def extract_audio_bytes(wav_file: str) -> bytes:
    with wave.open(wav_file, 'rb') as wav_file:
        channels = wav_file.getnchannels()
        sample_width = wav_file.getsampwidth()
        sample_rate = wav_file.getframerate()
        num_frames = wav_file.getnframes()

        raw_audio_bytes = wav_file.readframes(num_frames)

    print(f'{len(raw_audio_bytes)} raw bytes.')
    print(f'Channels: {channels}      Width: {sample_width} bytes')
    print(f'sample: {sample_rate}     nframes: {num_frames}')

    return raw_audio_bytes

def write_raw_audio_bytes(file_name, raw_audio_bytes):
    with open(file_name, "wb") as raw_file:
        raw_file.write(raw_audio_bytes)



def load_raw_audio_bytes(file_path):
    with open(file_path, "rb") as raw_file:
        loaded_bytes = raw_file.read()
        return loaded_bytes

def load_remote_raw_audio_bytes(remote_bytes):
    with urllib.request.urlopen(remote_bytes) as response:
        raw_audio_bytes = response.read()
        return raw_audio_bytes

def load_remote_audio_library(audio_library):
    audio_library = audio_library.copy()
    for sound in audio_library:
        with urllib.request.urlopen(audio_library[sound]) as response:
            raw_audio_bytes = response.read()
            audio_library[sound] = raw_audio_bytes
    return audio_library


def play_sound(loaded_bytes):
    # How have I never used io library before now?!
    bytes_io = io.BytesIO()
    # Set header and load
    with wave.open(bytes_io, "wb") as wav_write:
        wav_write.setnchannels(CHANNELS)
        wav_write.setsampwidth(SAMPLE_WIDTH)
        wav_write.setframerate(SAMPLE_RATE)
        wav_write.writeframes(loaded_bytes)

    # print('playback started')
    winsound.PlaySound(bytes_io.getvalue(), winsound.SND_MEMORY)
    # print('playback finished.')

def play(audio_bytes):
    play_thread = threading.Thread(target=play_sound, args=(audio_bytes,))
    play_thread.start()
    return play_thread


if __name__ == '__main__':
    # audio_bytes = load_remote_raw_audio_bytes()
    # play(audio_bytes)

    # al = load_remote_audio_library(audio_library)

    raw_audio_bytes = extract_audio_bytes(input_wav_path)
    write_raw_audio_bytes(raw_output_path, raw_audio_bytes)
    play(load_raw_audio_bytes(raw_output_path))
    # play(al['printer'])
    time.sleep(5)
    # play(al['cash_register'])
    # time.sleep(1.5)
