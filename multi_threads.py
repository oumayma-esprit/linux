import pyttsx3
import speech_recognition as sr
from datetime import datetime
import threading
import random
import queue
import requests
import os
import subprocess
from urllib.parse import urlparse

# Initialize the speech synthesis engine
engine = pyttsx3.init()

speak_lock = threading.Lock()

def speak(text):
    global speak_lock
    try:
        with speak_lock:
            engine.say(text)
            engine.runAndWait()
    except Exception as e:
        print(f"Error speaking: {e}")

def record_audio():
    r = sr.Recognizer()
    with sr.Microphone() as source:
        print("Listening...")
        audio = r.listen(source)
        voice_data = ''
        try:
            voice_data = r.recognize_google(audio, language='en-US')
            print("Recognized: " + voice_data)
        except sr.UnknownValueError:
            speak("I didn't understand what you said.")
        except sr.RequestError:
            speak("Please check your internet connection.")
    return voice_data

def recognize_speech(recognition_queue):
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        speak("Say something...")
        print("Say something...")
        audio = recognizer.listen(source)
        try:
            text = recognizer.recognize_google(audio, language='en-US')
            print(f"You said: {text}")
            recognition_queue.put(text.strip().lower())
        except sr.UnknownValueError:
            speak("I didn't understand what you said.")
            recognition_queue.put("")
        except sr.RequestError:
            speak("Speech recognition service error.")
            recognition_queue.put("")

# List to store downloaded file names
downloaded_files = []
mutex = threading.Lock()

def download_file(url):
    response = requests.get(url, stream=True)
    response.raise_for_status()  # Raise an exception for HTTP errors

    # Extract the file name from the URL
    parsed_url = urlparse(url)
    file_name = os.path.join(dest_folder, os.path.basename(parsed_url.path))

    with open(file_name, 'wb') as f:
        for chunk in response.iter_content(chunk_size=1024):
            if chunk:
                f.write(chunk)

    print(f"Download complete: {file_name}")

    with mutex:
        downloaded_files.append(file_name)

def download_photo(urls):
    threads = []
    for url in urls:
        thread = threading.Thread(target=download_file, args=(url,))
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()

    print("All downloads are complete.")

    # Display the downloaded files
    print("Downloaded files:")
    for file in downloaded_files:
        print(file)

    open_downloads_in_firefox()

def open_downloads_in_firefox():
    # Open the download folder in Firefox
    folder_path = os.path.abspath(dest_folder)
    firefox_command = f"firefox file://{folder_path}"
    
    # Start Firefox 
    process = subprocess.Popen(firefox_command, shell=True)
    process.wait()  # Wait for Firefox to close

    # After Firefox closes, restart greeting and listening
    greet_and_listen()


urls = [
    'https://img.freepik.com/photos-gratuite/lezard-animal-dans-nature-multicolore-gros-plan-ia-generative_188544-9072.jpg?size=626&ext=jpg&ga=GA1.1.2008272138.1721174400&semt=sph',
    'https://cdn.britannica.com/34/235834-050-C5843610/two-different-breeds-of-cats-side-by-side-outdoors-in-the-garden.jpg?w=400&h=300&c=crop',
    'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSVoFq3XlAYVa5ThUCMFuzv_C7zei7KhT9Nag&s',
]
dest_folder = 'downloads'

# Create the destination folder if it does not exist
os.makedirs(dest_folder, exist_ok=True)

# Shared data structure for the game
shared_data = {
    "secret_number": random.choice(["zero", "one"]),
    "guess": None,
    "attempts": 0,
    "game_over": False
}

data_lock = threading.Lock()
guess_semaphore = threading.Semaphore(0)
space_semaphore = threading.Semaphore(1)

def respond(voice_data):
    if 'play' in voice_data:
        speak('Launching the game')
        start_game()
    elif 'download' in voice_data or 'photo' in voice_data:
        speak('Downloading the photo')
        download_photo(urls)
    elif 'music' in voice_data:
        speak('Playing music')
        play_music()
    elif 'time' in voice_data:
        get_time()
    elif 'date' in voice_data:
        get_date()
    else:
        speak('I cannot understand you, please try again.')

def start_game():
    global shared_data
    print("Game started!")
    speak("Welcome to the Secret Number game!")
    speak("Try to guess the secret number: 'zero' or 'one'.")

    recognition_queue = queue.Queue()

    producer_thread = threading.Thread(target=producer, args=(recognition_queue,))
    consumer_thread = threading.Thread(target=consumer)

    producer_thread.start()
    consumer_thread.start()

    producer_thread.join()
    consumer_thread.join()

def producer(recognition_queue):
    global shared_data
    while not shared_data["game_over"]:
        speak("Guess the secret number: 'zero' or 'one'")
        recognition_thread = threading.Thread(target=recognize_speech, args=(recognition_queue,))
        recognition_thread.start()
        recognition_thread.join()  # Wait for speech recognition to finish

        guess = recognition_queue.get()
        print(f"Producer heard: {guess}")
        
        if guess in ['zero', 'one']:
            space_semaphore.acquire()  # Wait for space for a new guess
            with data_lock:
                shared_data["guess"] = guess
            guess_semaphore.release()  # Indicate that a guess is ready
        else:
            speak("Please provide a valid number: 'zero' or 'one'.")

def consumer():
    global shared_data
    while not shared_data["game_over"]:
        guess_semaphore.acquire()
        with data_lock:
            guess = shared_data["guess"]
            shared_data["attempts"] += 1
            print(f"Guess: {guess}, Secret Number: {shared_data['secret_number']}, Attempts: {shared_data['attempts']}")
            if guess == shared_data["secret_number"]:
                shared_data["game_over"] = True
                print("Correct guess!")
                speak(f"Congratulations! You found the secret number {shared_data['secret_number']} in {shared_data['attempts']} attempts.")
                speak("Exiting the game.")
                os._exit(0)  # Exit the script upon correct guess
            else:
                print("Incorrect guess. Try again.")
                speak("Try again.")
            shared_data["guess"] = None
        space_semaphore.release()

def greet_and_listen():
    speak("Choose 'play' to play a game or 'download' to download a photo or 'play music' or 'get time' or 'get date'.")
    while True:
        voice_data = record_audio()
        respond(voice_data)

play_music_lock = threading.Lock()

def play_music():
    with play_music_lock:
        speak("What song would you like to hear?")
        song = record_audio()
        
        if song:
            speak("Playing " + song)
            search_url = f"https://www.youtube.com/results?search_query={song}"
            
            # Open the music search URL in Firefox and wait for it to close
            firefox_command = ['firefox', search_url]
            process = subprocess.Popen(firefox_command)
            process.wait()  # Wait for Firefox to close

    # After Firefox closes, restart greeting and listening
    greet_and_listen()

time_date_lock = threading.Lock()

def get_time():
    global time_date_lock
    with time_date_lock:
        now = datetime.now()
        speak("It is " + now.strftime("%H:%M"))

def get_date():
    global time_date_lock
    with time_date_lock:
        now = datetime.now()
        speak("Today is " + now.strftime("%d %B %Y"))

if _name_ == "_main_":
    print("Hello")
    greet_and_listen()
