from midi2audio import FluidSynth


# Create a FluidSynth instance
fs = FluidSynth()


# Convert MIDI to audio
fs.midi_to_audio('C:/Users/carla/maestro-v3.0.0/2008/MIDI-Unprocessed_01_R1_2008_01-04_ORIG_MID--AUDIO_01_R1_2008_wav--3.midi', 'output_audio.wav')

# Close the FluidSynth instance
fs.close()
