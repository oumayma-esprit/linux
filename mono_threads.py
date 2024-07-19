import cv2
import pytesseract
import pyttsx3
import speech_recognition as sr
import pywhatkit
from datetime import datetime
import random
import time
import requests
import os
import subprocess
from urllib.parse import urlparse
import sys
import webbrowser

# Initialize the speech synthesis engine
engine = pyttsx3.init()

# Configuration for Tesseract OCR
pytesseract.pytesseract.tesseract_cmd = r'/usr/bin/tesseract'  # Adjust the path for Ubuntu

def speak(text):
    try:
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
    downloaded_files.append(file_name)

def download_photo(urls):
    for url in urls:
        download_file(url)

    print("All downloads are complete.")

    print("Downloaded files:")
    for file in downloaded_files:
        print(file)

    open_downloads_in_firefox()

def open_downloads_in_firefox():
    folder_path = os.path.abspath(dest_folder)
    firefox_command = f"firefox file://{folder_path}"
    subprocess.Popen(firefox_command, shell=True)

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

def greeting():
    speak("Hello, how can I assist you? Choose between 'play', 'download a photo', 'play music', 'get time', or 'get date'.")

def start_game():
    print("Game started!")
    speak("Welcome to the Secret Number game!")
    speak("Try to guess the secret number: 'zero' or 'one'.")
    secret_number = random.choice(["zero", "one"])
    attempts = 0

    while True:
        speak("Guess the secret number: 'zero' or 'one'")
        guess = record_audio()
        attempts += 1
        print(f"Guess: {guess}, Secret Number: {secret_number}, Attempts: {attempts}")

        if guess == secret_number:
            speak(f"Congratulations! You found the secret number {secret_number} in {attempts} attempts.")
            speak("Exiting the game.")
            break
        else:
            speak("Try again.")

def play_music():
    speak("What song would you like to hear?")
    song = record_audio()
    speak("Playing " + song)
    
    # Open one tab in Firefox with the song search results
    search_url = f"https://www.youtube.com/results?search_query={song}"
    webbrowser.open(search_url)

def get_time():
    now = datetime.now()
    speak("It is " + now.strftime("%H:%M"))

def get_date():
    now = datetime.now()
    speak("Today is " + now.strftime("%d %B %Y"))

urls = [
    'https://img.freepik.com/photos-gratuite/lezard-animal-dans-nature-multicolore-gros-plan-ia-generative_188544-9072.jpg?size=626&ext=jpg&ga=GA1.1.2008272138.1721174400&semt=sph',
    'https://cdn.britannica.com/34/235834-050-C5843610/two-different-breeds-of-cats-side-by-side-outdoors-in-the-garden.jpg?w=400&h=300&c=crop',
    'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSVoFq3XlAYVa5ThUCMFuzv_C7zei7KhT9Nag&s',
]
dest_folder = 'downloads'

# Create the destination folder if it does not exist
os.makedirs(dest_folder, exist_ok=True)

downloaded_files = []

if __name__ == "__main__":
    greeting()
    while True:
        voice_data = record_audio()
        respond(voice_data)
