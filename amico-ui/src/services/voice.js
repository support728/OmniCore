const importMeta = import.meta;

const VOICE_ID = importMeta.env?.VITE_ELEVENLABS_VOICE_ID || "YOUR_VOICE_ID";
const API_KEY = importMeta.env?.VITE_ELEVENLABS_API_KEY || "YOUR_API_KEY";
const VOICE_URL = `https://api.elevenlabs.io/v1/text-to-speech/${VOICE_ID}`;

let activeAudio = null;
let activeAudioUrl = null;

function cleanupAudio() {
  if (activeAudio) {
    activeAudio.onended = null;
    activeAudio.onerror = null;
    activeAudio = null;
  }

  if (activeAudioUrl) {
    URL.revokeObjectURL(activeAudioUrl);
    activeAudioUrl = null;
  }
}

export function stopSpeaking() {
  if (activeAudio) {
    activeAudio.pause();
    activeAudio.currentTime = 0;
  }

  cleanupAudio();
}

export async function speakText(text) {
  const content = String(text || "").trim();
  if (!content) {
    return;
  }

  stopSpeaking();

  const response = await fetch(VOICE_URL, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "xi-api-key": API_KEY,
    },
    body: JSON.stringify({
      text: content,
      voice_settings: {
        stability: 0.45,
        similarity_boost: 0.75,
      },
    }),
  });

  if (!response.ok) {
    throw new Error("Voice request failed.");
  }

  const audioBlob = await response.blob();
  activeAudioUrl = URL.createObjectURL(audioBlob);

  const audio = new Audio(activeAudioUrl);
  activeAudio = audio;

  await new Promise((resolve, reject) => {
    audio.onended = () => {
      cleanupAudio();
      resolve(undefined);
    };

    audio.onerror = () => {
      cleanupAudio();
      reject(new Error("Audio playback failed."));
    };

    const playPromise = audio.play();
    if (playPromise) {
      playPromise.catch((error) => {
        cleanupAudio();
        reject(error);
      });
    }
  });
}