package com.example.wuziqi;

import android.content.Context;
import android.media.AudioAttributes;
import android.media.AudioFormat;
import android.media.AudioManager;
import android.media.AudioTrack;
import android.util.Log;

public class SoundManager {
    private static final String TAG = "SoundManager";
    private Context context;
    private AudioTrack placeAudioTrack;
    private AudioTrack winAudioTrack;
    private int sampleRate = 44100;
    private float volume = 0.3f;

    public SoundManager(Context context) {
        this.context = context;
    }

    public void playPlaceSound() {
        // Generate a short "click" sound (800Hz for 100ms)
        generateTone(800, 100);
    }

    public void playWinSound() {
        // Generate a pleasant win sound (C note at 523Hz for 1000ms)
        generateTone(523, 1000);
    }

    private void generateTone(int frequency, int durationInMs) {
        int numSamples = durationInMs * sampleRate / 1000;
        double sample[] = new double[numSamples];
        byte[] generatedSound = new byte[2 * numSamples];

        // Fill the sample array with a sine wave
        for (int i = 0; i < numSamples; ++i) {
            sample[i] = Math.sin(2 * Math.PI * i / (sampleRate / frequency));
        }

        // Convert to 16 bit PCM sound array
        // Assumes the sample buffer is normalized between -1.0 and 1.0
        int idx = 0;
        for (int i = 0; i < numSamples; ++i) {
            // Scale to maximum amplitude of signed 16-bit number (32767)
            short shortVal = (short) (sample[i] * 32767 * volume);
            // In 16 bit WAV PCM, first byte is the low order byte
            generatedSound[idx++] = (byte) (shortVal & 0x00ff);
            generatedSound[idx++] = (byte) ((shortVal & 0xff00) >>> 8);
        }

        // Create and play the audio track
        AudioTrack audioTrack = new AudioTrack(
            new AudioAttributes.Builder()
                .setUsage(AudioAttributes.USAGE_GAME)
                .setContentType(AudioAttributes.CONTENT_TYPE_SONIFICATION)
                .build(),
            new AudioFormat.Builder()
                .setEncoding(AudioFormat.ENCODING_PCM_16BIT)
                .setSampleRate(sampleRate)
                .setChannelMask(AudioFormat.CHANNEL_OUT_STEREO)
                .build(),
            generatedSound.length,
            AudioTrack.MODE_STATIC,
            AudioManager.AUDIO_SESSION_ID_GENERATE
        );

        audioTrack.write(generatedSound, 0, generatedSound.length);
        audioTrack.play();
        
        // Release the track after playing
        new Thread(() -> {
            try {
                Thread.sleep(durationInMs + 100); // Wait for tone to finish + buffer time
                audioTrack.release();
            } catch (InterruptedException e) {
                Log.e(TAG, "Error releasing audio track: " + e.getMessage());
            }
        }).start();
    }

    public void release() {
        // Audio tracks are released after playing in generateTone method
    }
}