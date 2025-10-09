using UnityEngine;
using Meta.WitAi.TTS.Utilities;

public class SpeechOutput : MonoBehaviour
{
    [SerializeField] private TTSSpeaker _speaker;
    public NewSpeechCapture speechCap;

    private void Update()
    {
        speechCap.enableMic = !_speaker.IsSpeaking;
    }


    public void Speak(string text)
    {
        Debug.Log("[STATUS] Speaking text...");
        _speaker.Speak(text);
    }

    public void StopSpeaking()
    {
        _speaker.Stop();
    }
}   