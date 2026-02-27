using UnityEngine;
using Meta.WitAi.TTS.Utilities;

public class SpeechOutput : MonoBehaviour
{
    [SerializeField] private TTSSpeaker _speaker;
    public NewSpeechCapture speechCap;

    private void Update()
    {
        if (speechCap == null || _speaker == null)
        {
            return;
        }
        bool waitingForServer = speechCap.ngrok != null && speechCap.ngrok.IsRequestInFlight;
        speechCap.enableMic = !_speaker.IsSpeaking && !waitingForServer;
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
