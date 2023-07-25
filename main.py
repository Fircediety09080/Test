from kivy.app import App
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.filechooser import FileChooserListView
from kivy.clock import Clock
from kivy.core.audio import SoundLoader
from kivy.utils import get_color_from_hex


import os
import random

from mutagen.mp3 import MP3


class MusicPlayerApp(App):
    def build(self):
        self.title = 'Music Player'
        self.layout = BoxLayout(orientation="vertical", spacing=5, padding=10)



        # Create the file chooser
        self.file_chooser = FileChooserListView(
            path=os.path.expanduser("~"),
            filters=['*.mp3'],
        )
        self.layout.add_widget(self.file_chooser)

        # Create the current time label
        self.current_time_label = Label(text="Current Time: 0:00")
        self.layout.add_widget(self.current_time_label)

        # Create the file name label
        self.file_name_label = Label(text="File: ")
        self.layout.add_widget(self.file_name_label)

        # create play/pause button
        self.play_pause_button = Button(text='Play', size_hint=(1, 0.2))
        self.play_pause_button.bind(on_press=self.toggle_play_pause)
        self.layout.add_widget(self.play_pause_button)

        # Create the shuffle button
        self.shuffle_button = Button(text='Shuffle', size_hint=(1, 0.2))
        self.shuffle_button.bind(on_press=self.toggle_shuffle)
        self.shuffle_button.background_color = get_color_from_hex('#FFFFFF')
        self.layout.add_widget(self.shuffle_button)

        # Create the skip button
        self.skip_button = Button(text='Skip', size_hint=(1, 0.2))
        self.skip_button.bind(on_press=self.skip_file)
        self.layout.add_widget(self.skip_button)

        # Create the go back button
        self.back_button = Button(text='Previous File', size_hint=(1, 0.2))
        self.back_button.bind(on_press=self.Go_back)
        self.layout.add_widget(self.back_button)

        self.sound = None  # Initialize the sound attribute
        self.paused = False  # Track pause state
        self.current_time = 0  # Track current playback time
        self.file_queue = []  # Initialize the file queue
        self.is_paused = False
        self.updating_time = False
        self.storeTime = 0
        self.selected_file = None #store the selected file path
        self.is_playing = False
        self.is_shuffle_enabled = False


        return self.layout

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.is_skipping = False  # initialize skipping flag

    def play_selected_file(self, instance):
        selected_file = self.file_chooser.selection
        if selected_file:
            try:
                if self.sound and self.sound.state == 'play':
                    self.sound.stop()  # Stop the current sound

                audio = MP3(selected_file[0])
                duration = audio.info.length
                if duration > 0:
                    # Get the directory path of the selected file
                    directory = os.path.dirname(selected_file[0])
                    # Get all the files in the same directory with the ".mp3" extension
                    files_in_directory = [os.path.join(directory, f) for f in os.listdir(directory) if
                                          f.endswith('.mp3')]

                    if files_in_directory:
                        # Clear the existing file queue
                        self.file_queue.clear()
                        # Add all the files in the directory to the queue
                        self.file_queue.extend(files_in_directory)

                    if not self.is_playing:
                        self.file_queue.append(selected_file[0])
                        self.play_next_file()
                    else:
                        # If already playing, insert the selected file after the current playing file
                        self.file_queue.insert(1, selected_file[0])

                    self.file_name_label.text = "File: {}".format(os.path.basename(selected_file[0]))
                else:
                    self.show_popup('Error', 'Selected file has a duration of 0.')
            except Exception as e:
                self.show_popup('Error', str(e))
            self.selected_file = selected_file[0]  # Update the selected file attribute
            self.print_file_queue()  # Print the queue after adding files from the folder
        else:
            self.show_popup('Error', 'No file selected.')

    def toggle_play_pause(self, instance):
        if self.sound:
            if self.sound.state == 'play':
                print('State: play')
                self.pause_audio()
            else:
                print('State: pause')
                self.resume_audio()
        else:
            self.play_selected_file(None)

    def play_next_file(self):
        if self.file_queue:
            if self.sound:
                self.sound.unbind(on_stop=self.on_sound_stop)
                self.sound.stop()

            if self.is_shuffle_enabled:  # Check if shuffle mode is enabled
                # Get a random file from the queue
                next_file = random.choice(self.file_queue)
            else:
                # Get the next file from the front of the queue
                next_file = self.file_queue.pop(0)

            # Load the next file as sound
            sound = SoundLoader.load(next_file)
            if sound:
                self.sound = sound
                sound.bind(on_stop=self.on_sound_stop)
                self.update_current_time(None)
                sound.play()
                print("Playing:", next_file)
                self.is_playing = True
                self.is_skipping = False  # Reset the is_skipping flag to False
        else:
            self.sound = None
            self.file_name_label.text = "File: "
            self.is_playing = False

    def stop_audio(self):
        if self.sound:
            self.sound.stop()  # Stop the sound

    def skip_file(self, instance):
        if self.sound:
            self.stop_audio()

            if self.file_queue:
                next_file = self.file_queue.pop(0)  # Remove the first file from the queue
                self.file_name_label.text = "File: {}".format(os.path.basename(next_file))  # Update the file label
                self.play_next_file()  # Play the first file in the queue
                self.is_skipping = True  # Set the skipping flag to True to avoid playing the next file twice
            else:
                self.sound = None
                self.file_name_label.text = "File: "
                self.is_playing = False  # Set the is_playing flag to False when the queue is empty
        else:
            self.show_popup('Info', 'No more files to play.')




    def print_file_queue(self):
        print("File Queue:")
        for index, file in enumerate(self.file_queue, start=1):
            print(f"{index}. {file}")
    def pause_audio(self):
        if self.sound and self.sound.state == 'play':
            print('pause has been called')
            self.current_time = self.sound.get_pos()  # Store the current time
            self.is_paused = True
            self.stop_audio()  # Stop the audio playback
            self.play_pause_button.text = 'Play'  # Change the button text to 'Pause'

    def resume_audio(self):
        print(self.is_paused)
        if self.sound:
            if not self.is_paused:
                print('right code execution')  # Print statement should be inside the if block
                self.sound.seek(self.current_time)
                self.is_paused = False  # Reset the pause state
                self.sound.play()  # Start playing the audio
                self.play_pause_button.text = 'Pause'  # Change the button text to 'Pause'




    def update_current_time(self, dt):
        if self.sound and self.sound.state == 'play' and not self.is_paused:
            self.current_time = self.sound.get_pos()  # Update the current time
            self.current_time_label.text = "Current Time: {}".format(self.format_time(self.current_time))



        if self.is_paused:
            self.play_pause_button.text = 'Play'  # Change the button text to 'Play' when paused
        else:
            self.play_pause_button.text = 'Pause'  # Change the button text to 'Pause' when playing

        if not self.is_paused:
            Clock.schedule_once(self.update_current_time, 0.1)  # Schedule the next update only if not paused



    def format_time(self, time):
        minutes = int(time // 60)
        seconds = int(time % 60)
        return "{:d}:{:02d}".format(minutes, seconds)

    def shuffle_files(self, instance):
        random.shuffle(self.file_queue)
        if self.sound.state == 'stop':
            print('Code execution correct')
        print("Shuffle mode enabled: ", self.is_shuffle_enabled)
        self.print_file_queue()  # Print the queue after shuffling

    def toggle_shuffle(self, instance):
        self.is_shuffle_enabled = not self.is_shuffle_enabled

        if self.is_shuffle_enabled:
            self.shuffle_files(None)
            self.shuffle_button.background_color = get_color_from_hex("#0000FF")  # Blue color for enabled

        else:
            self.shuffle_button.background_color = get_color_from_hex("#FFFFFF")  # White color for disabled

    def on_file_finished(self, dt):
        self.stop_audio()  # Stop and unload the current sound
        self.current_time = 0  # Reset the current time
        self.paused = False  # Reset the paused state
        self.update_current_time(None)  # Update the current time immediately
        self.move_to_next_file()  # Move to the next file

    def move_to_next_file(self):
        current_file = self.file_chooser.selection
        if current_file:
            current_index = self.file_chooser.files.index(current_file[0])
            if current_index < len(self.file_chooser.files) - 1:
                next_file = self.file_chooser.files[current_index + 1]
                if next_file not in self.file_queue:  # Check if the next file is not already in the queue
                    self.file_queue.append(next_file)  # Add the next file to the queue
            else:
                self.show_popup('Info', 'No more files to play.')

    def on_sound_stop(self, instance):
        if self.is_skipping:
            self.is_skipping = False
            self.stop_audio()
            return

        if self.sound and self.sound.state == 'stop':
            if self.is_paused:
                self.is_paused = False
            else:
                self.update_current_time(None)  # Schedule an immediate update of the current time

        if self.is_shuffle_enabled and not self.is_skipping:
            self.play_next_file()
        else:
            self.move_to_next_file()  # Move to the next file

    def show_popup(self, title, content):
        popup_layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        popup_label = Label(text=content, size_hint=(1, 0.8))
        popup_button = Button(text='OK', size_hint=(1, 0.2))
        popup_layout.add_widget(popup_label)
        popup_layout.add_widget(popup_button)

        popup = Popup(title=title, content=popup_layout, size_hint=(None, None), size=(400, 200))
        popup_button.bind(on_press=popup.dismiss)

        popup.open()


if __name__ == '__main__':
    MusicPlayerApp().run()