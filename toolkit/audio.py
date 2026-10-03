import io
import threading
import time
import urllib.request
import wave
import winsound
from threading import Thread


CHANNELS: int = 2
SAMPLE_WIDTH: int = 2
SAMPLE_RATE: int = 44100

INPUT_WAV_PATH: str = r'../assets/source_audio/printer_noise.wav'
RAW_OUTPUT_PATH: str = r'../assets/generated/printer_noise_audio_bytes'

REMOTE_SOUNDS: dict[str, str] = {'ds9_ops_button_1': r'https://github.com/Kaz95/stdlib-only-toolkit/raw/refs/heads/dev/assets'
                                     r'/generated/ds9_ops_button_1_audio_bytes',

                 'cash_register': r'https://github.com/Kaz95/stdlib-only-toolkit/raw/refs/heads/dev/assets/generated'
                                  r'/kaching_audio_bytes',

                 'printer': r'https://github.com/Kaz95/stdlib-only-toolkit/raw/refs/heads/dev/assets/generated'
                            r'/printer_noise_audio_bytes'}


def extract_audio_bytes(wav_file: str) -> bytes:
    """Extract audio bytes from a WAV file. Print metadata to terminal."""
    with wave.open(wav_file, 'rb') as wav_file:
        channels = wav_file.getnchannels()
        sample_width = wav_file.getsampwidth()
        sample_rate = wav_file.getframerate()
        num_frames = wav_file.getnframes()

        audio_bytes = wav_file.readframes(num_frames)

    print(f'{len(audio_bytes)} raw bytes.')
    print(f'Channels: {channels}      Width: {sample_width} bytes')
    print(f'sample: {sample_rate}     nframes: {num_frames}')

    return audio_bytes

def write_audio_bytes(file_name: str, audio_bytes: bytes) -> None:
    """Write raw audio bytes to a WAV file."""
    with open(file_name, "wb") as raw_file:
        raw_file.write(audio_bytes)



def load_audio_bytes_from_file(file_path: str) -> bytes:
    """Load raw audio bytes from a file."""
    with open(file_path, "rb") as raw_file:
        loaded_bytes = raw_file.read()
        return loaded_bytes


def load_remote_sounds(remote_sounds: dict[str, str]) -> dict[str, bytes]:
    """Load remote sound library."""
    sound_bytes = remote_sounds.copy()
    for sound in sound_bytes:
        with urllib.request.urlopen(sound_bytes[sound]) as response:
            audio_bytes = response.read()
            sound_bytes[sound] = audio_bytes
    return sound_bytes


def _play_sound(audio_bytes: bytes) -> None:
    """Rebuild wav from meta info and raw bytes. Then play sound."""
    bytes_io = io.BytesIO()
    # Set header and load
    with wave.open(bytes_io, "wb") as wav_write:
        wav_write.setnchannels(CHANNELS)
        wav_write.setsampwidth(SAMPLE_WIDTH)
        wav_write.setframerate(SAMPLE_RATE)
        wav_write.writeframes(audio_bytes)

    winsound.PlaySound(bytes_io.getvalue(), winsound.SND_MEMORY)

def play_sound(audio_bytes: bytes) -> Thread:
    """Play sound on a separate thread."""
    play_thread = threading.Thread(target=_play_sound, args=(audio_bytes,))
    play_thread.start()
    return play_thread


if __name__ == '__main__':
    # audio_bytes = load_remote_raw_audio_bytes()
    # play(audio_bytes)

    al = load_remote_sounds(REMOTE_SOUNDS)

    # raw_audio_bytes = extract_audio_bytes(INPUT_WAV_PATH)
    # write_audio_bytes(RAW_OUTPUT_PATH, raw_audio_bytes)
    # play_sound(load_audio_bytes_from_file(RAW_OUTPUT_PATH))
    play_sound(al['printer'])
    time.sleep(5)
    # play(al['cash_register'])
    # time.sleep(1.5)
